from pathlib import Path
import pytest
from .helpers import REPO_ROOT

@pytest.fixture
def scenario_path():
    def _resolve(rel: str) -> str:
        return str(REPO_ROOT / "tests" / rel)
    return _resolve