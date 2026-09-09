from collections.abc import Iterable
from dataclasses import dataclass

from market_intelligence.contracts.market import Incident, MarketFeatures
from market_intelligence.contracts.snapshot import MarketSnapshot
from market_intelligence.replay.engine import ReplayResult, replay_snapshots

from .detector import AnomalyDetector
from .features import RollingFeatureCalculator


@dataclass(frozen=True)
class DetectionRun:
    replay: ReplayResult
    incidents: tuple[Incident, ...]
    final_features: dict[tuple[str, str], MarketFeatures]


def detect_snapshots(
    snapshots: Iterable[MarketSnapshot],
    *,
    calculator: RollingFeatureCalculator | None = None,
    detector: AnomalyDetector | None = None,
) -> DetectionRun:
    """Replay normalized snapshots through features and deterministic rules."""

    feature_calculator = calculator or RollingFeatureCalculator()
    anomaly_detector = detector or AnomalyDetector()
    incidents: list[Incident] = []
    final_features: dict[tuple[str, str], MarketFeatures] = {}

    def handle(snapshot: MarketSnapshot) -> None:
        features = feature_calculator.calculate(snapshot)
        final_features[(snapshot.source, snapshot.ticker)] = features
        incidents.extend(anomaly_detector.evaluate(snapshot, features))

    replay = replay_snapshots(snapshots, handle)
    return DetectionRun(
        replay=replay,
        incidents=tuple(incidents),
        final_features=final_features,
    )
