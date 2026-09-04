import json
from pathlib import Path

import pytest


@pytest.fixture
def kalshi_fixture_dir() -> Path:
    return Path("tests/fixtures/kalshi")


@pytest.fixture
def market_pages(kalshi_fixture_dir: Path) -> list[dict[str, object]]:
    return [
        json.loads((kalshi_fixture_dir / "markets-page-1.json").read_text(encoding="utf-8")),
        json.loads((kalshi_fixture_dir / "markets-page-2.json").read_text(encoding="utf-8")),
    ]
