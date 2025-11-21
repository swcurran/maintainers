import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "generate-maintainers.py"

def run_generator(repo, project, config, list_only=False, no_fetch=True):
    args = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repo", repo,
        "--project", project,
        "--config", config,
    ]

    if no_fetch:
        args.append("--no-fetch")

    if list_only:
        args.append("--list-only")

    proc = subprocess.run(
        args,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            f"Generator failure:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    return proc.stdout