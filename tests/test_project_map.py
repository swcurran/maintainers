import sys
from subprocess import run
from .helpers import SCRIPT_PATH, REPO_ROOT
import pytest


def run_gen(repo, cfg, no_fetch=True):
    """Helper to invoke generator with auto project detection."""
    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo", repo,
        "--config", cfg,
    ]
    if no_fetch:
        args.append("--no-fetch")

    proc = run(args, cwd=str(REPO_ROOT), capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Generator failure:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )
    return proc.stdout


def test_project_map_matched(snapshot, scenario_path):
    """
    Repo should match the regex in project_map and auto-assign a project.
    """
    cfg = scenario_path("projectmap/maintainer_config.yaml")
    out = run_gen("acapy-storage", cfg)
    snapshot.assert_match(out, "projectmap_matched.md")


def test_project_map_unmatched(snapshot, scenario_path):
    """
    Repo should NOT match anything in project_map → project = "".
    """
    cfg = scenario_path("projectmap/maintainer_config.yaml")
    out = run_gen("totally-different-repo", cfg)
    snapshot.assert_match(out, "projectmap_unmatched.md")