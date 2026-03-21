import os
from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_epub():
    path = FIXTURES_DIR / "sample.epub"
    assert path.exists(), "Run tests/create_fixture.py to generate fixture"
    return str(path)


@pytest.fixture
def tmp_output(tmp_path):
    return str(tmp_path / "output")
