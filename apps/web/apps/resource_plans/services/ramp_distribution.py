from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Sequence

from apps.resource_plans.constants import Progression, RampPattern

_QUANTUM = Decimal("0.25")


class RampDistributionService:
    """Pure computation, no DB access — used inline by AllocationEngineService."""

    @staticmethod
    def _round_quantum(value: Decimal) -> Decimal:
        return (value / _QUANTUM).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * _QUANTUM

    @staticmethod
    def _pattern_weights(pattern: str, n: int) -> list[Decimal]:
        if n <= 0:
            return []
        if pattern == RampPattern.RAMP_UP:
            return [Decimal(i + 1) for i in range(n)]
        if pattern == RampPattern.RAMP_DOWN:
            return [Decimal(n - i) for i in range(n)]
        if pattern == RampPattern.RAMP_UP_DOWN:
            return [Decimal(min(i + 1, n - i)) for i in range(n)]
        if pattern == RampPattern.RAMP_UP_STEADY:
            ramp_len = max(1, n // 3)
            return [Decimal(min(i + 1, ramp_len)) for i in range(n)]
        if pattern == RampPattern.STEADY_DOWN:
            ramp_len = max(1, n // 3)
            up_steady = [min(i + 1, ramp_len) for i in range(n)]
            return [Decimal(w) for w in reversed(up_steady)]
        if pattern == RampPattern.STEPPED:
            num_steps = min(4, n)
            block_size = -(-n // num_steps)  # ceil division
            return [Decimal((i // block_size) + 1) for i in range(n)]
        # FLAT and CUSTOM (segments absent) both fall back to equal weight.
        return [Decimal(1) for _ in range(n)]

    @classmethod
    def _segment_percentages(cls, segments: Sequence[Any]) -> list[Decimal]:
        percentages: list[Decimal] = []
        for segment in sorted(segments, key=lambda s: s.segment_order):
            duration = segment.duration
            start = Decimal(segment.start_percentage)
            end = Decimal(segment.end_percentage)
            step_count = segment.step_count or min(duration, 4)
            for i in range(duration):
                t = Decimal(i) / Decimal(duration - 1) if duration > 1 else Decimal(0)
                if segment.progression == Progression.LINEAR:
                    pct = start + (end - start) * t
                elif segment.progression == Progression.EXPONENTIAL:
                    pct = start + (end - start) * (t * t)
                elif segment.progression == Progression.LOGARITHMIC:
                    pct = start + (end - start) * t.sqrt()
                elif segment.progression == Progression.STEPPED:
                    block_size = -(-duration // step_count)  # ceil division
                    step_index = i // block_size
                    total_steps = -(-duration // block_size) - 1
                    step_t = (
                        Decimal(step_index) / Decimal(total_steps)
                        if total_steps > 0
                        else Decimal(0)
                    )
                    pct = start + (end - start) * step_t
                else:  # Progression.FLAT
                    pct = start
                percentages.append(pct)
        return percentages

    @classmethod
    def distribute(
        cls,
        total_days: Decimal,
        sprint_count: int,
        ramp_pattern: str,
        segments: Sequence[Any] | None,
        max_days_per_sprint: Decimal | None,
    ) -> list[Decimal]:
        if sprint_count <= 0 or total_days <= 0:
            return [Decimal("0")] * max(sprint_count, 0)

        segment_driven = bool(segments)
        if segments:
            weights = cls._segment_percentages(segments)
        else:
            weights = cls._pattern_weights(ramp_pattern, sprint_count)

        total_weight = sum(weights) or Decimal(1)
        proportions = [w / total_weight for w in weights]

        raw_days = [total_days * p for p in proportions]
        rounded_days = [cls._round_quantum(d) for d in raw_days]

        # Rounding each sprint independently can drift the sum away from
        # total_days by a few quantum steps — true it up before capping so
        # the cap/redistribute logic below starts from an exact total.
        drift = cls._round_quantum(total_days - sum(rounded_days))
        idx = 0
        step = _QUANTUM if drift > 0 else -_QUANTUM
        remaining_drift = abs(drift)
        while remaining_drift > 0 and rounded_days:
            i = idx % len(rounded_days)
            candidate = rounded_days[i] + step
            if candidate >= 0:
                rounded_days[i] = candidate
                remaining_drift -= _QUANTUM
            idx += 1
            if idx > len(rounded_days) * 4:
                break

        if max_days_per_sprint is None:
            return rounded_days

        cap = Decimal(max_days_per_sprint)
        if not segment_driven and ramp_pattern == RampPattern.FLAT:
            return cls._cap_with_redistribution(rounded_days, cap)
        # Ramp patterns (and segment-driven curves) cap without
        # redistribution, deliberately trading total-day precision to
        # preserve the intended shape.
        return [min(d, cap) for d in rounded_days]

    @classmethod
    def _cap_with_redistribution(
        cls, days: list[Decimal], cap: Decimal
    ) -> list[Decimal]:
        capped = [min(d, cap) for d in days]
        leftover = sum(days) - sum(capped)
        if leftover <= 0:
            return capped

        room = [cap - d for d in capped]
        while leftover > 0:
            progressed = False
            for i in range(len(capped)):
                if leftover <= 0:
                    break
                if room[i] <= 0:
                    continue
                give = min(_QUANTUM, room[i], leftover)
                if give <= 0:
                    continue
                capped[i] += give
                room[i] -= give
                leftover -= give
                progressed = True
            if not progressed:
                break
        return capped
