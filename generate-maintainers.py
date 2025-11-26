#!/usr/bin/env python3
# generate-maintainers.py

import sys
import argparse
import requests
import yaml
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
    """Convert GitHub UI URLs to ?raw=true, leave local paths untouched."""
    if not url.startswith(("http://", "https://")):
        # Local file path → return unchanged
        return url

    # Already a raw URL or already has ?raw=true
    if "raw.githubusercontent.com" in url or "?raw=true" in url:
        return url

    # Convert GitHub UI URL
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
        parent = load_config_with_extends(cfg["extends"])
        return merge_configs(parent, cfg)
    return cfg


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


def collect_repo_members(repo_name: str, governance: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Return dict: {username -> {role1, role2}}."""
    repo_entry = next((r for r in governance.get("repositories", []) if r.get("name") == repo_name), None)
    if not repo_entry:
        raise ValueError(f"Repository '{repo_name}' not found in governance YAML.")

    teams = {t["name"]: t for t in governance.get("teams", [])}
    members: Dict[str, Set[str]] = {}

    for team_name, role in repo_entry.get("teams", {}).items():
        team_info = teams.get(team_name)
        if not team_info:
            continue
        all_members = set(team_info.get("maintainers", []) + team_info.get("members", []))
        for user in all_members:
            members.setdefault(user, set()).add(role)

    return members


def substitute_vars(text: str, vars: Dict[str, str]) -> str:
    """Replace {var} in before/after template text."""
    # Conditional blocks: {{ if var }} ... {{ else }} ... {{ endif }}
    import re
    def cond_repl(match):
        var = match.group(1).strip()
        body_if = match.group(2)
        body_else = match.group(3) or ""
        val = vars.get(var, "")
        return body_if if val else body_else

    text = re.sub(
        r"\{\{\s*if\s+([a-zA-Z0-9_]+)\s*\}\}(.*?)(?:\{\{\s*else\s*\}\}(.*?))?\{\{\s*endif\s*\}\}",
        cond_repl,
        text,
        flags=re.DOTALL,
    )

    # Simple {var} and {var:default}
    for k, v in vars.items():
        text = text.replace("{" + k + "}", v)
    import re
    def default_repl(m):
        key = m.group(1)
        default = m.group(2)
        return vars.get(key, default)
    text = re.sub(r"\{([a-zA-Z0-9_]+):([^}]+)\}", default_repl, text)

    return text


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
        role_str = ", ".join(sorted(roles))
        lines.append(f"| {user} | {name} | {email} | {company} | {role_str} |")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate MAINTAINERS.md")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output")
    parser.add_argument("--token")
    parser.add_argument("--no-fetch", action="store_true")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args()
    maintainers_config_ui_link = args.config
    maintainers_config_raw_link = to_raw_url(args.config)

    cfg = load_config_with_extends(args.config)
    eprint(f"Loaded maintainer config: {args.config}")

    before_text = cfg.get("before_text", "")
    after_text = cfg.get("after_text", "")
    organization = cfg.get("organization", "Organization")
    gov_org = cfg.get("gov_org", "Governance Repository")
    yaml_link = cfg.get("yaml_link")

    if not yaml_link:
        raise ValueError("yaml_link missing in configuration.")

    yaml_raw_link = to_raw_url(yaml_link)
    eprint(f"Governance YAML RAW URL: {yaml_raw_link}")

    governance = load_yaml(yaml_raw_link)
    repo_members = collect_repo_members(args.repo, governance)

    session = requests.Session()
    if args.no_fetch:
        user_info = {u: ("", "", "") for u in repo_members}
    else:
        user_info = {u: gh_get_user(u, session, args.token) for u in repo_members}

    table = build_table(repo_members, user_info)

    if args.list_only:
        print(table)
        return

    vars = dict(
        repo=args.repo,
        project=args.project,
        organization=organization,
        gov_org=gov_org,
        yaml_link=yaml_link,
        yaml_raw_link=yaml_raw_link,
        maintainers_config_link=maintainers_config_ui_link,
        maintainers_config_raw_link=maintainers_config_raw_link,
    )

    result = (
        substitute_vars(before_text, vars).rstrip()
        + "\n\n"
        + table
        + "\n\n"
        + substitute_vars(after_text, vars).lstrip()
    )

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)


if __name__ == "__main__":
    main()