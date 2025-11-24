from subprocess import run
import sys
from .helpers import SCRIPT_PATH, REPO_ROOT

def run_generator_tmpl(repo, project, config, no_fetch=True):
    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo", repo,
        "--project", project,
        "--config", config,
    ]

    if no_fetch:
        args.append("--no-fetch")

    proc = run(args, cwd=str(REPO_ROOT), capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(
            f"Generator failure:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    return proc.stdout


def test_templating(snapshot, scenario_path):
    """
    Ensures conditional templating and defaults work.
    """

    cfg = scenario_path("templating/maintainer_config.yaml")

    output = run_generator_tmpl(
        repo="repo-basic",
        project="MyProject",
        config=cfg,
    )

    snapshot.assert_match(output, "templating.md")