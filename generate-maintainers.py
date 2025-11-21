#!/usr/bin/env python3
# generate-maintainers.py (updated)

import sys
import argparse
import requests
import yaml
from typing import Dict, Any, Optional, Set, Tuple

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def load_yaml(path_or_url: str) -> Dict[str, Any]:
    if path_or_url.startswith(("http://", "https://")):
        r = requests.get(path_or_url)
        r.raise_for_status()
        return yaml.safe_load(r.text)
    with open(path_or_url, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def ensure_raw_github_url(url: str) -> str:
    if "raw.githubusercontent.com" in url:
        return url
    if "github.com" in url and "/blob/" in url:
        after = url.split("github.com/")[1]
        parts = after.split("/")
        if len(parts) >= 4 and parts[2] == "blob":
            org = parts[0]
            repo = parts[1]
            branch = parts[3]
            filepath = "/".join(parts[4:])
            return f"https://raw.githubusercontent.com/{org}/{repo}/{branch}/{filepath}"
    return url

def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
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
    cfg = load_yaml(cfg_path)
    if "extends" in cfg:
        parent_cfg = load_config_with_extends(cfg["extends"])
        return merge_configs(parent_cfg, cfg)
    return cfg

def gh_get_user(username: str, session: requests.Session, token: Optional[str]) -> Tuple[str, str, str]:
    url = f"https://api.github.com/users/{username}"
    headers = {"Authorization": f"token {token}"} if token else {}
    r = session.get(url, headers=headers)
    if r.status_code != 200:
        return ("", "", "")
    data = r.json()
    return (data.get("name") or "", data.get("email") or "", data.get("company") or "")

def collect_repo_members(repo_name: str, governance: Dict[str, Any]) -> Dict[str, Set[str]]:
    repo_entry = None
    for r in governance.get("repositories", []):
        if r.get("name") == repo_name:
            repo_entry = r
            break
    if not repo_entry:
        raise ValueError(f"Repository '{repo_name}' not found in governance YAML.")
    team_defs = {t["name"]: t for t in governance.get("teams", [])}
    members: Dict[str, Set[str]] = {}
    for team_name, role in repo_entry.get("teams", {}).items():
        team_info = team_defs.get(team_name)
        if not team_info:
            continue
        all_members = set(team_info.get("maintainers", []) + team_info.get("members", []))
        for user in all_members:
            members.setdefault(user, set()).add(role)
    return members

def substitute_vars(text: str, vars: Dict[str, str]) -> str:
    for k, v in vars.items():
        text = text.replace("{" + k + "}", v)
    return text

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

    cfg = load_config_with_extends(args.config)
    eprint(f"Loaded maintainer config: {args.config}")

    before_text = cfg.get("before_text", "")
    after_text = cfg.get("after_text", "")
    organization = cfg.get("organization", "Organization")
    gov_org = cfg.get("gov_org", "Governance Repository")
    yaml_ui_link = cfg.get("yaml_link")

    if not yaml_ui_link:
        raise ValueError("yaml_link missing in config.")

    yaml_raw_link = ensure_raw_github_url(yaml_ui_link)
    eprint(f"Governance YAML RAW URL: {yaml_raw_link}")

    governance = load_yaml(yaml_raw_link)
    repo_members = collect_repo_members(args.repo, governance)

    session = requests.Session()
    user_info = {}
    if not args.no_fetch:
        for user in repo_members.keys():
            user_info[user] = gh_get_user(user, session, args.token)
    else:
        for user in repo_members.keys():
            user_info[user] = ("", "", "")

    lines = ["## Current Maintainers\n",
             "| GitHub ID | Name | Email | Company | Roles |",
             "|-----------|------|-------|---------|-------|"]

    for user, roles in sorted(repo_members.items()):
        name, email, company = user_info[user]
        roles_str = ", ".join(sorted(roles))
        lines.append(f"| {user} | {name} | {email} | {company} | {roles_str} |")

    table = "\n".join(lines)

    if args.list_only:
        result = table
    else:
        vars = dict(
            repo=args.repo,
            project=args.project,
            organization=organization,
            gov_org=gov_org,
            yaml_link=yaml_ui_link,
            yaml_raw_link=yaml_raw_link,
        )
        result = substitute_vars(before_text, vars).rstrip() + "\n\n" + table + "\n\n" + substitute_vars(after_text, vars).lstrip()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()
