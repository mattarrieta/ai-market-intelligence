from pathlib import Path

import pytest


@pytest.fixture
def golden_dataset_path() -> Path:
    return Path("datasets/golden/market-incidents-v1.jsonl")
