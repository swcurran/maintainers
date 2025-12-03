import pytest
from .helpers import run_generator

def test_repo_snapshot(snapshot, scenario_path):
    cfg = scenario_path("repo/maintainer_config.yaml")
    out = run_generator("repo-basic", "RepoProject", cfg)
    snapshot.assert_match(out, "repo.md")

def test_project_snapshot(snapshot, scenario_path):
    cfg = scenario_path("project/maintainer_config.yaml")
    out = run_generator("repo-project", "ProjectA", cfg)
    snapshot.assert_match(out, "project.md")

def test_org_snapshot(snapshot, scenario_path):
    cfg = scenario_path("org/maintainer_config.yaml")
    out = run_generator("repo-org", "OrgProject", cfg)
    snapshot.assert_match(out, "org.md")

def test_list_only(snapshot, scenario_path):
    cfg = scenario_path("listonly/maintainer_config.yaml")
    out = run_generator("repo-basic", "ListOnly", cfg, list_only=True)
    snapshot.assert_match(out, "list_only.md")

def test_missing_repo_raises(scenario_path):
    from subprocess import run
    import sys
    from pathlib import Path
    from .helpers import SCRIPT_PATH, REPO_ROOT

    cfg = scenario_path("errors/missing_config.yaml")
    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo", "missing-repo",
        "--project", "BadProject",
        "--config", cfg,
        "--no-fetch",
    ]
    p = run(args, cwd=str(REPO_ROOT), capture_output=True, text=True)
    assert p.returncode != 0
    assert "not found in CLOWarden configuration" in p.stderr