#!/usr/bin/env python3
# generate-maintainers.py

import sys
import argparse
import requests
import yaml
import re
from typing import Dict, Any, Optional, Set, Tuple


def eprint(*args, **kwargs):
    """Print to stderr."""
    print(*args, file=sys.stderr, **kwargs)


def load_yaml(path_or_url: str) -> Dict[str, Any]:
    """Load YAML from local file or HTTP(S) URL."""
    if path_or_url.startswith(("http://", "https://")):
        r = requests.get(path_or_url)
        r.raise_for_status()
        return yaml.safe_load(r.text)
    with open(path_or_url, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def to_raw_url(url: str) -> str:
    """
    Convert GitHub UI URLs to ?raw=true.
    Leave local paths untouched. Leave raw.githubusercontent.com untouched.
    """
    if not url.startswith(("http://", "https://")):
        return url

    if "raw.githubusercontent.com" in url or "?raw=true" in url:
        return url

    # Convert GitHub blob URLs automatically
    return url + ("&raw=true" if "?" in url else "?raw=true")


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Recursive merge of YAML config dicts."""
    result = dict(base)
    for k, v in override.items():
        if k == "extends":
            continue
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = merge_configs(result[k], v)
        else:
            result[k] = v
    return result


def load_config_with_extends(cfg_path: str) -> Dict[str, Any]:
    """Load config, recursively resolving 'extends'."""
    cfg = load_yaml(cfg_path)
    if "extends" in cfg:
        parent_cfg = load_config_with_extends(cfg["extends"])
        return merge_configs(parent_cfg, cfg)
    return cfg


def detect_project(repo: str, cfg: Dict[str, Any]) -> str:
    """
    Return project name based on regex rules in project_map.

    project_map:
      - name: "ACA-Py"
        repos:
          - "^acapy"
          - "^aries-cloudagent-python"
    """
    project_map = cfg.get("project_map", [])
    for entry in project_map:
        name = entry.get("name", "")
        patterns = entry.get("repos", []) or []
        for pat in patterns:
            try:
                if re.search(pat, repo):
                    return name or ""
            except re.error:
                # Bad regex; ignore and continue
                continue
    return ""  # No match → empty string


def gh_get_user(username: str, session: requests.Session, token: Optional[str]) -> Tuple[str, str, str]:
    """Fetch GitHub user profile fields."""
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {token}"} if token else {}
    r = session.get(url, headers=headers)
    if r.status_code != 200:
        return ("", "", "")
    data = r.json()
    return (
        data.get("name") or "",
        data.get("email") or "",
        data.get("company") or "",
    )


def collect_repo_members(repo_name: str, clowarden_cfg: Dict[str, Any]) -> Dict[str, Set[str]]:
    """
    Return {username -> {role1, role2}} based on a CLOWarden access configuration.
    """
    repo_entry = next(
        (r for r in clowarden_cfg.get("repositories", []) if r.get("name") == repo_name),
        None,
    )
    if not repo_entry:
        raise ValueError(f"Repository '{repo_name}' not found in CLOWarden configuration.")

    teams = {t["name"]: t for t in clowarden_cfg.get("teams", [])}
    members: Dict[str, Set[str]] = {}

    for team_name, role in repo_entry.get("teams", {}).items():
        team_info = teams.get(team_name)
        if not team_info:
            continue
        all_members = set(team_info.get("maintainers", []) + team_info.get("members", []))
        for user in all_members:
            members.setdefault(user, set()).add(role)

    return members


# ---------------------------------------------------------------------------
# Templating: conditionals + default placeholders
# ---------------------------------------------------------------------------

def render_conditionals(text: str, vars: Dict[str, str]) -> str:
    """
    Process conditional blocks of the form:

      {{ if var }}
      ...
      {{ else }}
      ...
      {{ endif }}

    Truthiness is based on vars[var] being a non-empty string.
    """
    lines = text.splitlines()
    out_lines = []
    stack = []  # (active, cond_value, in_else, parent_active)

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("{{") and stripped.endswith("}}"):
            inner = stripped[2:-2].strip()

            if inner.startswith("if "):
                var_name = inner[3:].strip()
                cond_val = bool(vars.get(var_name, ""))
                parent_active = stack[-1][0] if stack else True
                active = parent_active and cond_val
                stack.append([active, cond_val, False, parent_active])
                continue

            if inner == "else":
                if stack:
                    active, cond_val, _, parent_active = stack[-1]
                    new_active = parent_active and (not cond_val)
                    stack[-1] = [new_active, cond_val, True, parent_active]
                continue

            if inner == "endif":
                if stack:
                    stack.pop()
                continue

        include = True
        for active, _, _, _ in stack:
            if not active:
                include = False
                break
        if include:
            out_lines.append(line)

    return "\n".join(out_lines)


def apply_default_placeholders(text: str, vars: Dict[str, str]) -> str:
    """
    Handle {var:Default} syntax.

    - If vars[var] is non-empty, use that.
    - Else, use Default.
    """
    def repl(match: re.Match) -> str:
        name = match.group(1)
        default = match.group(2)
        val = vars.get(name, "")
        return val if val else default

    pattern = re.compile(r"\{([A-Za-z0-9_]+):([^}]+)\}")
    return pattern.sub(repl, text)


def apply_simple_placeholders(text: str, vars: Dict[str, str]) -> str:
    """Handle {var} placeholders (after defaults have been processed)."""
    def repl(match: re.Match) -> str:
        name = match.group(1)
        return vars.get(name, "")

    pattern = re.compile(r"\{([A-Za-z0-9_]+)\}")
    return pattern.sub(repl, text)


def render_template(text: str, vars: Dict[str, str]) -> str:
    """Full template rendering: conditionals → defaults → simple vars."""
    # 1. Conditionals
    text = render_conditionals(text, vars)
    # 2. Defaulted placeholders {var:default}
    text = apply_default_placeholders(text, vars)
    # 3. Simple placeholders {var}
    text = apply_simple_placeholders(text, vars)
    return text


# ---------------------------------------------------------------------------
# Markdown table
# ---------------------------------------------------------------------------

def build_table(repo_members: Dict[str, Set[str]], user_info: Dict[str, Tuple[str, str, str]]) -> str:
    """Return markdown table as string."""
    lines = [
        "## Current Maintainers",
        "",
        "| GitHub ID | Name | Email | Company | Roles |",
        "|-----------|------|-------|---------|-------|",
    ]
    for user, roles in sorted(repo_members.items()):
        name, email, company = user_info[user]
        roles_str = ", ".join(sorted(roles))
        lines.append(f"| {user} | {name} | {email} | {company} | {roles_str} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate MAINTAINERS.md")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=False, default=None)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output")
    parser.add_argument("--token")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()

    # Load generator config with extends
    cfg = load_config_with_extends(args.config)
    eprint(f"Loaded generator config: {args.config}")

    # Determine final project value:
    # - If --project is omitted or "", auto-detect via project_map
    # - Else, use provided value
    if args.project is None or args.project == "":
        project = detect_project(args.repo, cfg)
        eprint(f"Auto-detected project: '{project}'")
    else:
        project = args.project
        eprint(f"Using provided project: '{project}'")

    before_text = cfg.get("before_text", "")
    after_text = cfg.get("after_text", "")
    organization = cfg.get("organization", "Organization")
    governance_repo = cfg.get("governance_repo", "Governance Repository")

    clowarden_file = cfg.get("clowarden_file")
    if not clowarden_file:
        raise ValueError("clowarden_file missing in configuration.")

    clowarden_raw_file = to_raw_url(clowarden_file)
    eprint(f"CLOWarden RAW URL: {clowarden_raw_file}")

    clowarden_cfg = load_yaml(clowarden_raw_file)
    repo_members = collect_repo_members(args.repo, clowarden_cfg)

    session = requests.Session()
    if args.no_fetch:
        user_info = {u: ("", "", "") for u in repo_members}
    else:
        user_info = {u: gh_get_user(u, session, args.token) for u in repo_members}

    table = build_table(repo_members, user_info)

    if args.list_only:
        result = table
    else:
        vars = dict(
            repo=args.repo,
            project=project,
            organization=organization,
            governance_repo=governance_repo,
            clowarden_file=clowarden_file,
            clowarden_raw_file=clowarden_raw_file,
            maintainers_config_link=args.config,
            maintainers_config_raw_link=to_raw_url(args.config),
        )
        result = (
            render_template(before_text, vars).rstrip()
            + "\n\n"
            + table
            + "\n\n"
            + render_template(after_text, vars).lstrip()
        )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)


if __name__ == "__main__":
    main()