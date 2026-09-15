"""
Tests for planner/optimizer.py -- no activity overlap, duplicate
prevention, opening-hours compliance, budget ceiling, party suitability
(Section 40 testing strategy).
"""
from planner.optimizer import ScoredCandidate, build_day_plans


def _poi(name, category="beach", duration=120, cost=0, zone_id=1,
         opening_time=None, closing_time=None, **suitability):
    poi = dict(
        name=name, category=category, duration_minutes=duration, cost=cost,
        zone_id=zone_id, opening_time=opening_time, closing_time=closing_time,
        accessibility_level="high",
        morning_suitability=80, afternoon_suitability=80, evening_suitability=80,
        solo_suitability=70, couple_suitability=70, family_suitability=70,
        friends_suitability=70, seniors_suitability=70,
    )
    poi.update(suitability)
    return poi


def test_no_duplicate_activity_across_days():
    pois = [_poi(f"POI {i}", cost=100) for i in range(2)]
    candidates = [ScoredCandidate(poi=p, ml_score=90, zone_id=1) for p in pois]

    days, _ = build_day_plans(
        candidates=candidates, n_days=3, pace="packed", traveller_type="couple",
        mobility_need="none", per_day_soft_budget=None, zone_name_lookup={1: "Test Zone"},
    )

    used_names = []
    for day in days:
        for sched in day.scheduled:
            used_names.append(sched["poi"]["name"])
    assert len(used_names) == len(set(used_names)), "the same POI must not be scheduled twice"


def test_no_activity_overlap_within_a_day():
    # each period (morning/afternoon/evening) can hold at most one activity
    pois = [_poi(f"POI {i}", cost=0) for i in range(5)]
    candidates = [ScoredCandidate(poi=p, ml_score=80, zone_id=1) for p in pois]

    days, _ = build_day_plans(
        candidates=candidates, n_days=1, pace="packed", traveller_type="friends",
        mobility_need="none", per_day_soft_budget=None, zone_name_lookup={1: "Test Zone"},
    )

    periods = [sched["period"] for sched in days[0].scheduled]
    assert len(periods) == len(set(periods)), "at most one activity should be scheduled per period"


def test_opening_hours_hard_constraint_excludes_incompatible_activity():
    # this POI is only open 22:00-23:59, which never overlaps morning/afternoon/evening windows
    night_only = _poi("Midnight Market", opening_time="22:00", closing_time="23:59")
    candidates = [ScoredCandidate(poi=night_only, ml_score=99, zone_id=1)]

    days, notes = build_day_plans(
        candidates=candidates, n_days=1, pace="balanced", traveller_type="solo",
        mobility_need="none", per_day_soft_budget=None, zone_name_lookup={1: "Test Zone"},
    )
    assert days[0].scheduled == []
    assert any("no feasible activity" in n for n in notes)


def test_per_day_soft_budget_is_respected():
    expensive = _poi("Luxury Cruise", cost=5000)
    cheap = _poi("Free Beach Walk", cost=0)
    candidates = [
        ScoredCandidate(poi=expensive, ml_score=95, zone_id=1),
        ScoredCandidate(poi=cheap, ml_score=90, zone_id=1),
    ]

    days, _ = build_day_plans(
        candidates=candidates, n_days=1, pace="easy_going", traveller_type="couple",
        mobility_need="none", per_day_soft_budget=200, zone_name_lookup={1: "Test Zone"},
    )
    total_cost = sum(s["poi"]["cost"] for s in days[0].scheduled)
    assert total_cost <= 200 * 1.15  # optimizer allows up to a 15% soft overage, no more


def test_low_accessibility_excluded_for_wheelchair_need():
    inaccessible = _poi("Rocky Trail", accessibility_level="low")
    candidates = [ScoredCandidate(poi=inaccessible, ml_score=99, zone_id=1)]

    days, _ = build_day_plans(
        candidates=candidates, n_days=1, pace="balanced", traveller_type="seniors",
        mobility_need="wheelchair", per_day_soft_budget=None, zone_name_lookup={1: "Test Zone"},
    )
    scheduled_names = [s["poi"]["name"] for s in days[0].scheduled]
    assert "Rocky Trail" not in scheduled_names