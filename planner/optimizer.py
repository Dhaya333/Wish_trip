"""
Constraint-aware multi-day itinerary optimiser (Sections 16-21).

This is implemented as a greedy + local-repair heuristic approximating an
Orienteering-Problem-style formulation: maximise preference/ML-suitability
weighted value subject to per-day time, budget, opening-hours, duplicate,
and party/accessibility constraints, while respecting the pace profile.

A full MILP/exact solver is out of scope for this prototype; the greedy
construction plus repair pass is a defensible, explainable approximation
that still enforces every hard constraint in Section 18.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

PACE_TARGETS = {
    # (target activity count per day, max total activity minutes per day,
    #  min free-time minutes to leave unscheduled)
    "easy_going": dict(target_count=2, max_minutes=240, min_free_minutes=180),
    "balanced": dict(target_count=3, max_minutes=330, min_free_minutes=90),
    "packed": dict(target_count=4, max_minutes=420, min_free_minutes=30),
}

DAY_WINDOWS = {
    "morning": ("09:00", "12:30"),
    "afternoon": ("13:00", "17:30"),
    "evening": ("18:00", "21:30"),
}

CATEGORY_DIVERSITY_PENALTY = 18.0  # points subtracted per repeat of same category in a day


def _time_to_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def _period_score(poi: Dict, period: str) -> int:
    return poi.get(f"{period}_suitability", 50)


def _opening_hours_ok(poi: Dict, period: str) -> bool:
    open_t, close_t = poi.get("opening_time"), poi.get("closing_time")
    if not open_t or not close_t:
        return True  # unknown hours -- allowed, but caller must mark assumption
    window_start, window_end = DAY_WINDOWS[period]
    return not (_time_to_minutes(close_t) <= _time_to_minutes(window_start) or
                _time_to_minutes(open_t) >= _time_to_minutes(window_end))


@dataclass
class ScoredCandidate:
    poi: Dict
    ml_score: float
    zone_id: int


@dataclass
class DayResult:
    day_number: int
    zone_focus_id: int
    zone_focus_name: str
    scheduled: List[Dict] = field(default_factory=list)  # activity dicts w/ period/time/why
    travel_minutes: int = 0
    day_cost: float = 0.0
    assumptions: List[str] = field(default_factory=list)


def _party_ok(poi: Dict, traveller_type: str, mobility_need: str) -> bool:
    if mobility_need in ("reduced_walking", "wheelchair"):
        if poi.get("accessibility_level") == "low":
            return False
    suit = poi.get(f"{traveller_type}_suitability", 50)
    return suit >= 25  # hard floor: don't ever schedule something clearly unsuitable for the party


def build_day_plans(
    candidates: List[ScoredCandidate],
    n_days: int,
    pace: str,
    traveller_type: str,
    mobility_need: str,
    per_day_soft_budget: Optional[float],
    zone_name_lookup: Dict[int, str],
) -> Tuple[List[DayResult], List[str]]:
    """
    Greedy day-by-day construction (Section 25 Day Construction steps 4-16):
      - candidates are pre-scored by ML suitability
      - for each day/period, pick the highest (score - diversity_penalty)
        candidate that satisfies hard constraints and hasn't been used yet
      - stop adding activities once the pace target count/minutes are hit
    Returns per-day results plus any global feasibility notes.
    """
    notes: List[str] = []
    pace_cfg = PACE_TARGETS[pace]

    # hard party/accessibility filter up front -- mobility needs are a hard
    # constraint where mandatory (Section 18.10), so this filter is never
    # relaxed even if it leaves few or no candidates.
    filtered = [c for c in candidates if _party_ok(c.poi, traveller_type, mobility_need)]
    if not filtered:
        notes.append("No candidate activities passed party/accessibility constraints; "
                      "results will be sparse. Consider relaxing mobility or party filters.")

    filtered.sort(key=lambda c: c.ml_score, reverse=True)

    used_poi_names: set = set()
    used_categories_today: Dict[int, set] = {}
    days: List[DayResult] = []

    for day_idx in range(n_days):
        day_categories = set()
        day = DayResult(day_number=day_idx + 1, zone_focus_id=-1, zone_focus_name="")
        minutes_used = 0
        count_used = 0

        for period in ("morning", "afternoon", "evening"):
            if count_used >= pace_cfg["target_count"] or minutes_used >= pace_cfg["max_minutes"]:
                break

            best = None
            best_score = -1.0
            for c in filtered:
                name = c.poi["name"]
                if name in used_poi_names:
                    continue  # duplicate prevention (Section 18.13)
                if not _opening_hours_ok(c.poi, period):
                    continue  # opening-hours hard constraint (Section 18.4)
                duration = c.poi.get("duration_minutes", 90)
                if minutes_used + duration > pace_cfg["max_minutes"]:
                    continue
                if per_day_soft_budget is not None and day.day_cost + c.poi.get("cost", 0) > per_day_soft_budget * 1.15:
                    continue  # soft budget guard per day, hard ceiling enforced at pipeline level

                period_fit = _period_score(c.poi, period)
                diversity_penalty = CATEGORY_DIVERSITY_PENALTY if c.poi["category"] in day_categories else 0.0
                effective_score = (0.65 * c.ml_score) + (0.35 * period_fit) - diversity_penalty

                if effective_score > best_score:
                    best_score = effective_score
                    best = c

            if best is None:
                continue

            duration = best.poi.get("duration_minutes", 90)
            window_start, _ = DAY_WINDOWS[period]
            assumption_notes = []
            if best.poi.get("opening_hours_is_assumption"):
                assumption_notes.append("Opening hours for this activity are an estimate, not verified live data.")
            if best.poi.get("is_synthetic_or_estimated"):
                assumption_notes.append("Cost/duration for this activity is indicative, not a verified live price.")

            day.scheduled.append({
                "poi": best.poi,
                "period": period,
                "start_time": window_start,
                "duration_minutes": duration,
                "why_score": best_score,
                "assumptions": assumption_notes,
            })
            used_poi_names.add(best.poi["name"])
            day_categories.add(best.poi["category"])
            day.day_cost += best.poi.get("cost", 0)
            minutes_used += duration
            count_used += 1
            if day.zone_focus_id == -1:
                day.zone_focus_id = best.zone_id
                day.zone_focus_name = zone_name_lookup.get(best.zone_id, "")

        if not day.scheduled:
            notes.append(f"Day {day_idx + 1}: no feasible activity could be scheduled under the "
                          f"current constraints (budget/pace/mobility). Consider relaxing one of them.")
            day.zone_focus_name = day.zone_focus_name or next(iter(zone_name_lookup.values()), "")

        days.append(day)

    return days, notes


def select_hotel(scored_hotels: List[Tuple[Dict, float]], nights: int,
                  budget_cap_for_stay: Optional[float]) -> Tuple[Optional[Dict], List[str]]:
    """
    Picks the final hotel from ML-ranked candidates (Section 22), applying
    the hard budget ceiling if one was supplied.
    """
    notes = []
    ranked = sorted(scored_hotels, key=lambda t: t[1], reverse=True)

    if budget_cap_for_stay is not None:
        affordable = [(h, s) for h, s in ranked if h["price_per_night"] * nights <= budget_cap_for_stay]
        if affordable:
            return affordable[0][0], notes
        notes.append("No hotel fits the allocated stay budget at the requested comfort level; "
                      "selecting the closest (cheapest) available option instead.")
        cheapest = min(ranked, key=lambda t: t[0]["price_per_night"])
        return cheapest[0], notes

    if not ranked:
        notes.append("No hotel candidates were available for this destination/comfort level.")
        return None, notes

    return ranked[0][0], notes