"""
Synthetic traveller profile + interaction + label generation, per
MASTER_PROJECT.md Section 14 (Synthetic Training Label Strategy) and
Section 31 (Training Pipeline).

This is explicitly synthetic data used to train a model that approximates
a transparent utility function -- it does not represent real traveller
behaviour. See docs/SYNTHETIC_DATA_SPECIFICATION.md for the full spec.

The same utility function (`utility_score`) is reused as the rule-based
baseline described in Section 33 (Baseline 2).
"""
import random
from dataclasses import dataclass, field
from typing import Dict, List

INTERESTS = [
    "food", "culture", "nature", "beaches", "wellness", "adventure",
    "nightlife", "shopping", "history", "photography", "wildlife",
    "spirituality",
]
TRAVELLER_TYPES = ["solo", "couple", "family", "friends", "seniors"]
PACES = ["easy_going", "balanced", "packed"]


@dataclass
class SyntheticProfile:
    traveller_type: str
    adults: int
    children: int
    seniors: int
    budget_level: str  # low/medium/high
    pace: str
    mobility_need: str  # none/reduced_walking/wheelchair
    preferences: Dict[str, int] = field(default_factory=dict)


def _random_profile(rng: random.Random) -> SyntheticProfile:
    ttype = rng.choice(TRAVELLER_TYPES)
    adults = rng.randint(1, 2) if ttype in ("solo", "couple") else rng.randint(2, 4)
    children = rng.randint(0, 2) if ttype == "family" else 0
    seniors = rng.randint(1, 2) if ttype == "seniors" else 0
    prefs = {i: rng.randint(0, 100) for i in INTERESTS}
    return SyntheticProfile(
        traveller_type=ttype, adults=adults, children=children, seniors=seniors,
        budget_level=rng.choice(["low", "medium", "high"]),
        pace=rng.choice(PACES),
        mobility_need=rng.choice(["none", "none", "none", "reduced_walking", "wheelchair"]),
        preferences=prefs,
    )


def preference_match_score(profile: SyntheticProfile, poi_affinities: Dict[str, int]) -> float:
    """Weighted dot-product style match between preference vector and POI affinities, 0-100."""
    weights = profile.preferences
    total_weight = sum(weights.values()) or 1
    matched = sum(weights[i] * poi_affinities.get(i, 0) for i in INTERESTS)
    return min(100.0, matched / total_weight)


def party_suitability_score(profile: SyntheticProfile, item: dict) -> float:
    key = f"{profile.traveller_type}_suitability"
    return float(item.get(key, 50))


def pace_compatibility_score(profile: SyntheticProfile, item: dict) -> float:
    duration = item.get("duration_minutes", 90)
    if profile.pace == "easy_going":
        return 100.0 if duration <= 120 else max(0.0, 100 - (duration - 120) / 3)
    if profile.pace == "packed":
        return 100.0 if duration <= 150 else max(0.0, 100 - (duration - 150) / 5)
    return 100.0 if duration <= 135 else max(0.0, 100 - (duration - 135) / 4)


def budget_compatibility_score(profile: SyntheticProfile, item: dict) -> float:
    cost = item.get("cost", item.get("price_per_night", 0))
    caps = {"low": 800, "medium": 2500, "high": 8000}
    cap = caps[profile.budget_level]
    if cost <= cap:
        return 100.0
    return max(0.0, 100 - (cost - cap) / max(cap, 1) * 100)


def accessibility_compatibility_score(profile: SyntheticProfile, item: dict) -> float:
    if profile.mobility_need == "none":
        return 100.0
    level = item.get("accessibility_level", "unknown")
    mapping = {"high": 100.0, "medium": 60.0, "low": 20.0, "unknown": 40.0}
    return mapping.get(level, 40.0)


def utility_score(profile: SyntheticProfile, item: dict, is_hotel: bool = False,
                   rng: random.Random = None) -> float:
    """
    Transparent utility function (Section 14):

        + Preference Match
        + Party Suitability
        + Context Suitability (approximated here via time-of-day defaults)
        + Pace Compatibility
        + Budget Compatibility
        + Accessibility Compatibility
        + Quality/Popularity proxy
        - Cost Penalty (folded into budget compatibility)
        - Travel Burden (applied by the optimizer, not the base utility)
        - Context Conflict (n/a at this stage)

    Weighted sum normalised to 0-100, plus small Gaussian noise so a model
    trained on this label must learn the *relationship*, not the exact
    formula (Section 14).
    """
    rng = rng or random
    affinities = {i: item.get(f"affinity_{i}", 0) for i in INTERESTS} if not is_hotel else {}
    pref_match = preference_match_score(profile, affinities) if not is_hotel else 60.0
    party = party_suitability_score(profile, item)
    pace = pace_compatibility_score(profile, item) if not is_hotel else 100.0
    budget = budget_compatibility_score(profile, item)
    accessibility = accessibility_compatibility_score(profile, item)
    popularity = float(item.get("popularity_proxy", 50))

    weights = dict(pref=0.30, party=0.20, pace=0.10, budget=0.20,
                   accessibility=0.10, popularity=0.10)
    score = (
        weights["pref"] * pref_match
        + weights["party"] * party
        + weights["pace"] * pace
        + weights["budget"] * budget
        + weights["accessibility"] * accessibility
        + weights["popularity"] * popularity
    )
    noise = rng.gauss(0, 4)  # controlled noise, Section 14
    return max(0.0, min(100.0, score + noise))


def generate_training_rows(items: List[dict], n_profiles: int = 400, is_hotel: bool = False,
                            seed: int = 42):
    """
    Cross joins synthetic traveller profiles with candidate items (POIs or
    hotels) and computes the transparent-utility label for each pair.
    Profiles are generated independently per split by the caller passing a
    distinct seed, to avoid the train/test leakage described in Section 32.
    """
    rng = random.Random(seed)
    rows = []
    for _ in range(n_profiles):
        profile = _random_profile(rng)
        for item in items:
            label = utility_score(profile, item, is_hotel=is_hotel, rng=rng)
            row = {
                "traveller_type": profile.traveller_type,
                "adults": profile.adults,
                "children": profile.children,
                "seniors": profile.seniors,
                "budget_level": profile.budget_level,
                "pace": profile.pace,
                "mobility_need": profile.mobility_need,
                **{f"pref_{i}": profile.preferences[i] for i in INTERESTS},
                "item_id": item.get("name"),
                "item_cost": item.get("cost", item.get("price_per_night", 0)),
                "item_duration": item.get("duration_minutes", 0),
                "item_popularity": item.get("popularity_proxy", 50),
                "item_accessibility": item.get("accessibility_level", "unknown"),
                "item_party_suit": item.get(f"{profile.traveller_type}_suitability", 50),
                "label_suitability": round(label, 2),
            }
            if not is_hotel:
                row.update({f"affinity_{i}": item.get(f"affinity_{i}", 0) for i in INTERESTS})
            rows.append(row)
    return rows