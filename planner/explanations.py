"""
Structured, template-based explanation generation (Section 27).

No LLM is used. Every explanation is built directly from real scoring
signals available on the candidate (preference weights, POI affinities,
period fit, party suitability, cost) so the explanation always corresponds
to actual planner data.
"""
from typing import Dict, List

from ml.synthetic_data import INTERESTS

TOP_N_INTERESTS = 2


def _top_matching_interests(preferences: Dict[str, int], poi: Dict) -> List[str]:
    matches = []
    for interest in INTERESTS:
        pref_weight = preferences.get(interest, 0)
        affinity = poi.get(f"affinity_{interest}", 0)
        if pref_weight >= 50 and affinity >= 50:
            matches.append((interest, pref_weight * affinity))
    matches.sort(key=lambda x: x[1], reverse=True)
    return [m[0] for m in matches[:TOP_N_INTERESTS]]


def explain_activity(poi: Dict, preferences: Dict[str, int], period: str,
                      traveller_type: str) -> str:
    reasons = []

    top_interests = _top_matching_interests(preferences, poi)
    if top_interests:
        joined = " and ".join(top_interests)
        reasons.append(f"strongly matches your {joined} preference")

    period_fit = poi.get(f"{period}_suitability", 50)
    if period_fit >= 70:
        reasons.append(f"fits well in the {period}")

    party_suit = poi.get(f"{traveller_type}_suitability", 50)
    if party_suit >= 75:
        reasons.append(f"is well suited for a {traveller_type} trip")

    if poi.get("cost", 0) == 0:
        reasons.append("adds no extra activity cost")

    if not reasons:
        reasons.append("was the best available fit for this time slot given your other preferences")

    return "Selected because it " + ", ".join(reasons) + "."


def explain_hotel(hotel: Dict, comfort_level: str, traveller_type: str, budget_constrained: bool) -> str:
    reasons = [f"matches your requested {comfort_level} comfort level"]

    party_suit = hotel.get(f"{traveller_type}_suitability", 50)
    if party_suit >= 75:
        reasons.append(f"is well suited for a {traveller_type} trip")

    if budget_constrained:
        reasons.append("was the closest affordable option once the budget ceiling was applied")

    return "This hotel was chosen because it " + ", ".join(reasons) + "."


def day_summary(day_activities: List[str], zone_name: str, pace: str) -> str:
    if not day_activities:
        return f"No activities could be scheduled in {zone_name} under the current constraints."
    joined = ", ".join(day_activities)
    return (f"A {pace.replace('_', '-')}-paced day centred around {zone_name}, "
            f"covering {joined}.")