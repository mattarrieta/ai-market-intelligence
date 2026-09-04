"""Market data ingestion adapters and services."""

from .collector import CollectionResult, MarketCollector
from .featured import fetch_featured_market, select_featured_market
from .kalshi import KalshiClient, KalshiClientError, normalize_market
from .repository import SnapshotRepository

__all__ = [
    "CollectionResult",
    "KalshiClient",
    "KalshiClientError",
    "MarketCollector",
    "SnapshotRepository",
    "fetch_featured_market",
    "normalize_market",
    "select_featured_market",
]
