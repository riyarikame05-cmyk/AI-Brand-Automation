"""
V5 deterministic logo quality and diversity gate.

The gate intentionally separates:
1. hard rejection,
2. quality scoring,
3. same-batch diversity.

No runtime randomness is used.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass(frozen=True)
class QualityResult:
    accepted: bool
    score: float
    reasons: tuple[str, ...]
    metrics: dict

    def to_dict(self):
        return asdict(self)


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, float(value)))


def evaluate_candidate(
    *,
    element_count: int,
    max_elements: int,
    occupancy: float,
    contrast: float,
    small_size_survival: float,
    balance: float,
    silhouette_strength: float,
    semantic_relevance: float,
    distinctiveness: float,
    initial_integration: float = 0.5,
    disconnected_fragments: int = 0,
    cliche_detected: bool = False,
) -> dict:
    """
    Score one identity candidate on normalized 0..1 measurements.

    Hard failures reject a candidate even when its average score is high.
    """
    metrics = {
        "element_count": max(0, int(element_count)),
        "max_elements": max(1, int(max_elements)),
        "occupancy": _clamp(occupancy),
        "contrast": _clamp(contrast),
        "small_size_survival": _clamp(small_size_survival),
        "balance": _clamp(balance),
        "silhouette_strength": _clamp(silhouette_strength),
        "semantic_relevance": _clamp(semantic_relevance),
        "distinctiveness": _clamp(distinctiveness),
        "initial_integration": _clamp(initial_integration),
        "disconnected_fragments": max(0, int(disconnected_fragments)),
        "cliche_detected": bool(cliche_detected),
    }

    reasons = []

    if metrics["element_count"] > metrics["max_elements"]:
        reasons.append("too-many-elements")

    if metrics["occupancy"] < 0.22:
        reasons.append("symbol-too-small")

    if metrics["occupancy"] > 0.84:
        reasons.append("symbol-overfilled")

    if metrics["contrast"] < 0.42:
        reasons.append("weak-contrast")

    if metrics["small_size_survival"] < 0.56:
        reasons.append("fails-64px")

    if metrics["balance"] < 0.45:
        reasons.append("poor-balance")

    if metrics["silhouette_strength"] < 0.48:
        reasons.append("weak-silhouette")

    if metrics["semantic_relevance"] < 0.40:
        reasons.append("weak-semantic-signal")

    if metrics["disconnected_fragments"] > 2:
        reasons.append("fragmented-construction")

    if metrics["cliche_detected"]:
        reasons.append("cliche-construction")

    # Weighted score: readability and silhouette matter more than decoration.
    score = (
        metrics["small_size_survival"] * 0.18
        + metrics["silhouette_strength"] * 0.17
        + metrics["balance"] * 0.15
        + metrics["distinctiveness"] * 0.15
        + metrics["semantic_relevance"] * 0.14
        + metrics["contrast"] * 0.10
        + metrics["initial_integration"] * 0.07
        + (
            1.0
            - abs(metrics["occupancy"] - 0.55) / 0.55
        ) * 0.04
    )

    score = _clamp(score)

    # Hard rejection reasons cannot be averaged away.
    hard_failures = {
        "too-many-elements",
        "symbol-too-small",
        "symbol-overfilled",
        "weak-contrast",
        "fails-64px",
        "poor-balance",
        "weak-silhouette",
        "fragmented-construction",
        "cliche-construction",
    }

    accepted = (
        score >= 0.58
        and not any(reason in hard_failures for reason in reasons)
    )

    return QualityResult(
        accepted=accepted,
        score=round(score, 4),
        reasons=tuple(reasons),
        metrics=metrics,
    ).to_dict()


def feature_distance(a: dict, b: dict) -> float:
    """
    Distance between candidate feature signatures.

    Later these signatures can include perceptual raster hashes. The API
    already supports geometry/silhouette features without changing callers.
    """
    keys = (
        "occupancy",
        "balance",
        "silhouette_strength",
        "semantic_relevance",
        "initial_integration",
        "angularity",
        "openness",
        "symmetry",
    )

    values = []

    for key in keys:
        if key in a and key in b:
            values.append(
                abs(
                    _clamp(a[key])
                    - _clamp(b[key])
                )
            )

    if not values:
        return 1.0

    return sum(values) / len(values)


def select_diverse_candidates(
    candidates: Iterable[dict],
    count: int,
    minimum_distance: float = 0.10,
) -> list[dict]:
    """
    Greedy deterministic selection:
    highest quality first, then reject near-duplicates.
    """
    candidates = list(candidates)

    ranked = sorted(
        candidates,
        key=lambda item: (
            -float(item.get("quality", {}).get("score", 0.0)),
            str(item.get("variant_key", "")),
        ),
    )

    selected = []

    for candidate in ranked:
        quality = candidate.get("quality", {})

        if not quality.get("accepted", False):
            continue

        features = candidate.get("features", {})

        duplicate = any(
            feature_distance(
                features,
                previous.get("features", {}),
            ) < minimum_distance
            for previous in selected
        )

        if duplicate:
            continue

        selected.append(candidate)

        if len(selected) >= count:
            break

    return selected


def batch_diversity_score(candidates: Iterable[dict]) -> float:
    candidates = list(candidates)

    if len(candidates) < 2:
        return 1.0 if candidates else 0.0

    distances = []

    for i in range(len(candidates)):
        for j in range(i + 1, len(candidates)):
            distances.append(
                feature_distance(
                    candidates[i].get("features", {}),
                    candidates[j].get("features", {}),
                )
            )

    if not distances:
        return 0.0

    return round(
        _clamp(sum(distances) / len(distances)),
        4,
    )
