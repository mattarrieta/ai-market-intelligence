from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import NAMESPACE_URL, uuid5

from market_intelligence.contracts.enums import IncidentType, MarketHealth
from market_intelligence.contracts.market import Incident, MarketFeatures
from market_intelligence.contracts.snapshot import MarketSnapshot


@dataclass(frozen=True)
class DetectorPolicy:
    version: str = "rules-1.0.0"
    warmup_samples: int = 6
    price_shock_threshold: Decimal = Decimal("0.10")
    volume_zscore_threshold: Decimal = Decimal("5")
    spread_threshold: Decimal = Decimal("0.15")
    liquidity_decline_threshold: Decimal = Decimal("0.50")
    cooldown: timedelta = timedelta(minutes=5)

    def __post_init__(self) -> None:
        if not self.version:
            raise ValueError("version must not be empty")
        if self.warmup_samples < 2:
            raise ValueError("warmup_samples must be at least two")
        thresholds = {
            "price_shock_threshold": self.price_shock_threshold,
            "volume_zscore_threshold": self.volume_zscore_threshold,
            "spread_threshold": self.spread_threshold,
            "liquidity_decline_threshold": self.liquidity_decline_threshold,
        }
        for name, threshold in thresholds.items():
            if threshold <= 0:
                raise ValueError(f"{name} must be positive")
        if self.cooldown < timedelta(0):
            raise ValueError("cooldown must not be negative")


class AnomalyDetector:
    """Apply deterministic, versioned rules to calculated market features."""

    def __init__(self, policy: DetectorPolicy | None = None) -> None:
        self.policy = policy or DetectorPolicy()
        self._last_incident_at: dict[tuple[str, str, IncidentType], datetime] = {}

    def _in_cooldown(
        self,
        key: tuple[str, str, IncidentType],
        detected_at: datetime,
    ) -> bool:
        previous = self._last_incident_at.get(key)
        return previous is not None and detected_at - previous < self.policy.cooldown

    @staticmethod
    def _severity(value: Decimal, threshold: Decimal) -> Decimal:
        raw = min(Decimal(10), value / threshold * Decimal(5))
        return raw.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _incident(
        self,
        snapshot: MarketSnapshot,
        features: MarketFeatures,
        incident_type: IncidentType,
        magnitude: Decimal,
        threshold: Decimal,
    ) -> Incident | None:
        key = snapshot.source, snapshot.ticker, incident_type
        if self._in_cooldown(key, snapshot.observed_at):
            return None
        identity = "|".join(
            (
                self.policy.version,
                snapshot.source,
                snapshot.ticker,
                incident_type.value,
                snapshot.observed_at.isoformat(),
            )
        )
        incident = Incident(
            incident_id=str(uuid5(NAMESPACE_URL, identity)),
            ticker=snapshot.ticker,
            incident_type=incident_type,
            detected_at=snapshot.observed_at,
            severity=self._severity(magnitude, threshold),
            market_health=MarketHealth.LIVE,
            features=features,
            detector_version=self.policy.version,
        )
        self._last_incident_at[key] = snapshot.observed_at
        return incident

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        features: MarketFeatures,
    ) -> tuple[Incident, ...]:
        if features.observed_at != snapshot.observed_at:
            raise ValueError("feature and snapshot timestamps must match")
        if features.sample_count < self.policy.warmup_samples:
            return ()

        candidates: list[tuple[IncidentType, Decimal, Decimal]] = []
        if (
            features.price_change_5m is not None
            and abs(features.price_change_5m) >= self.policy.price_shock_threshold
        ):
            candidates.append(
                (
                    IncidentType.PRICE_SHOCK,
                    abs(features.price_change_5m),
                    self.policy.price_shock_threshold,
                )
            )
        if (
            features.volume_zscore is not None
            and features.volume_zscore >= self.policy.volume_zscore_threshold
        ):
            candidates.append(
                (
                    IncidentType.VOLUME_SPIKE,
                    features.volume_zscore,
                    self.policy.volume_zscore_threshold,
                )
            )
        if features.spread is not None and features.spread >= self.policy.spread_threshold:
            candidates.append(
                (IncidentType.SPREAD_ANOMALY, features.spread, self.policy.spread_threshold)
            )
        if (
            features.liquidity_decline is not None
            and features.liquidity_decline >= self.policy.liquidity_decline_threshold
        ):
            candidates.append(
                (
                    IncidentType.LIQUIDITY_SHOCK,
                    features.liquidity_decline,
                    self.policy.liquidity_decline_threshold,
                )
            )

        incidents = (
            self._incident(snapshot, features, incident_type, magnitude, threshold)
            for incident_type, magnitude, threshold in candidates
        )
        return tuple(incident for incident in incidents if incident is not None)
