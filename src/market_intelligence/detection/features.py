from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from market_intelligence.contracts.market import MarketFeatures
from market_intelligence.contracts.snapshot import MarketSnapshot


class OutOfOrderSnapshotError(ValueError):
    """Raised when a market receives non-increasing observation timestamps."""


@dataclass(frozen=True)
class FeaturePolicy:
    short_window: timedelta = timedelta(seconds=30)
    long_window: timedelta = timedelta(minutes=5)
    retention_window: timedelta = timedelta(minutes=30)
    minimum_volume_baseline: int = 3
    volume_deviation_floor: Decimal = Decimal("1")

    def __post_init__(self) -> None:
        if self.short_window <= timedelta(0):
            raise ValueError("short_window must be positive")
        if self.long_window < self.short_window:
            raise ValueError("long_window must not be shorter than short_window")
        if self.retention_window < self.long_window:
            raise ValueError("retention_window must not be shorter than long_window")
        if self.minimum_volume_baseline < 1:
            raise ValueError("minimum_volume_baseline must be at least one")
        if self.volume_deviation_floor <= 0:
            raise ValueError("volume_deviation_floor must be positive")


@dataclass(frozen=True)
class _Observation:
    snapshot: MarketSnapshot
    reference_price: Decimal | None
    volume_delta: Decimal


class RollingFeatureCalculator:
    """Maintain isolated rolling state and calculate deterministic market features."""

    def __init__(self, policy: FeaturePolicy | None = None) -> None:
        self.policy = policy or FeaturePolicy()
        self._history: dict[tuple[str, str], deque[_Observation]] = defaultdict(deque)

    @staticmethod
    def _midpoint(snapshot: MarketSnapshot) -> Decimal | None:
        if snapshot.yes_bid is None or snapshot.yes_ask is None:
            return None
        return (snapshot.yes_bid + snapshot.yes_ask) / Decimal(2)

    @classmethod
    def _reference_price(cls, snapshot: MarketSnapshot) -> Decimal | None:
        midpoint = cls._midpoint(snapshot)
        return midpoint if midpoint is not None else snapshot.last_price

    @staticmethod
    def _standard_deviation(values: list[Decimal]) -> Decimal | None:
        if len(values) < 2:
            return None
        mean = sum(values, Decimal(0)) / Decimal(len(values))
        variance = sum((value - mean) ** 2 for value in values) / Decimal(len(values))
        return variance.sqrt()

    @staticmethod
    def _price_change(
        history: deque[_Observation],
        current: _Observation,
        window: timedelta,
    ) -> Decimal | None:
        if current.reference_price is None:
            return None
        cutoff = current.snapshot.observed_at - window
        baseline = next(
            (
                item.reference_price
                for item in history
                if item.snapshot.observed_at >= cutoff and item.reference_price is not None
            ),
            None,
        )
        return current.reference_price - baseline if baseline is not None else None

    def _volume_zscore(
        self,
        history: deque[_Observation],
        current_delta: Decimal,
    ) -> Decimal | None:
        baseline = [item.volume_delta for item in history][-self.policy.minimum_volume_baseline :]
        if len(baseline) < self.policy.minimum_volume_baseline:
            return None
        mean = sum(baseline, Decimal(0)) / Decimal(len(baseline))
        deviation = self._standard_deviation(baseline) or Decimal(0)
        deviation = max(deviation, self.policy.volume_deviation_floor)
        return (current_delta - mean) / deviation

    def _liquidity_decline(
        self,
        history: deque[_Observation],
        current: MarketSnapshot,
    ) -> Decimal | None:
        if current.liquidity_dollars is None:
            return None
        cutoff = current.observed_at - self.policy.long_window
        previous = [
            item.snapshot.liquidity_dollars
            for item in history
            if item.snapshot.observed_at >= cutoff and item.snapshot.liquidity_dollars is not None
        ]
        if not previous:
            return None
        baseline = max(previous)
        if baseline == 0:
            return Decimal(0)
        return max(Decimal(0), (baseline - current.liquidity_dollars) / baseline)

    def calculate(self, snapshot: MarketSnapshot) -> MarketFeatures:
        key = snapshot.source, snapshot.ticker
        history = self._history[key]
        if history and snapshot.observed_at <= history[-1].snapshot.observed_at:
            raise OutOfOrderSnapshotError(
                f"snapshot time must increase for {snapshot.source}:{snapshot.ticker}"
            )

        previous_volume = history[-1].snapshot.volume if history else snapshot.volume
        volume_delta = max(Decimal(0), snapshot.volume - previous_volume)
        current = _Observation(snapshot, self._reference_price(snapshot), volume_delta)
        long_cutoff = snapshot.observed_at - self.policy.long_window
        recent_prices = [
            item.reference_price
            for item in history
            if item.snapshot.observed_at >= long_cutoff and item.reference_price is not None
        ]
        if current.reference_price is not None:
            recent_prices.append(current.reference_price)

        short_cutoff = snapshot.observed_at - self.policy.short_window
        short_volume = sum(
            (
                item.volume_delta
                for item in (*history, current)
                if item.snapshot.observed_at >= short_cutoff
            ),
            Decimal(0),
        )
        midpoint = self._midpoint(snapshot)
        spread = (
            snapshot.yes_ask - snapshot.yes_bid
            if snapshot.yes_bid is not None and snapshot.yes_ask is not None
            else None
        )
        features = MarketFeatures(
            sample_count=len(history) + 1,
            observed_at=snapshot.observed_at,
            midpoint=midpoint,
            spread=spread,
            price_change_30s=self._price_change(history, current, self.policy.short_window),
            price_change_5m=self._price_change(history, current, self.policy.long_window),
            volume_30s=short_volume,
            volume_delta=volume_delta,
            volume_zscore=self._volume_zscore(history, volume_delta),
            volatility_5m=self._standard_deviation(recent_prices),
            liquidity_dollars=snapshot.liquidity_dollars,
            liquidity_decline=self._liquidity_decline(history, snapshot),
        )

        history.append(current)
        retention_cutoff = snapshot.observed_at - self.policy.retention_window
        while history and history[0].snapshot.observed_at < retention_cutoff:
            history.popleft()
        return features
