"""
End-to-end integration tests for planner/pipeline.py against the seeded
Goa dataset (Section 36 -- example demonstration trips), run against a
throwaway SQLite database so the suite doesn't require PostgreSQL.
"""
import os
from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.init_db import reset_and_seed
from database.models import Base
import database.session as db_session_module
from planner.pipeline import run_planning_pipeline
from planner.schemas import PreferenceWeights, TripRequest

TEST_DB_PATH = "test_wishtrip.db"


@pytest.fixture(scope="module")
def db_session():
    # point the shared session module at an isolated test database, then seed it
    test_url = f"sqlite:///./{TEST_DB_PATH}"
    test_engine = create_engine(test_url, connect_args={"check_same_thread": False})
    db_session_module.engine = test_engine
    db_session_module.SessionLocal = sessionmaker(bind=test_engine)

    reset_and_seed()

    session = db_session_module.SessionLocal()
    yield session
    session.close()
    # On Windows, SQLite keeps the file locked until every connection made
    # through this engine is fully released -- dispose() closes the
    # connection pool so the file can actually be deleted afterwards.
    test_engine.dispose()
    if os.path.exists(TEST_DB_PATH):
        try:
            os.remove(TEST_DB_PATH)
        except PermissionError:
            # Best-effort cleanup only -- a leftover test DB file does not
            # affect correctness of the next run (reset_and_seed() drops
            # and recreates all tables on the next test session anyway).
            pass


def _make_request(traveller_type, preferences, pace, budget_total=60000,
                   hotel_comfort="standard", mobility_need="none"):
    return TripRequest(
        origin_city="Mumbai", destination="Goa",
        start_date=date(2026, 12, 10), end_date=date(2026, 12, 14), nights=4,
        traveller_type=traveller_type, adults=2, children=0, seniors=0,
        preference_weights=PreferenceWeights(**preferences),
        pace=pace, budget_total=budget_total, hotel_comfort=hotel_comfort,
        dietary_preference="no_preference", mobility_need=mobility_need,
        preferred_transport="balanced",
    )


def test_relaxed_couple_example_produces_a_feasible_multi_day_plan(db_session):
    # Section 36, Example A -- Relaxed Couple
    req = _make_request(
        "couple",
        dict(beaches=90, photography=80, food=70, wellness=60, nightlife=20),
        pace="easy_going",
    )
    plan = run_planning_pipeline(req, db_session)

    assert len(plan.days) == req.nights
    assert plan.hotel is not None
    assert plan.cost_breakdown.grand_total > 0


def test_adventure_friends_example_differs_from_relaxed_couple(db_session):
    # Section 36, Example B -- Adventure Friends; should produce a
    # meaningfully different plan from Example A.
    relaxed = run_planning_pipeline(_make_request(
        "couple", dict(beaches=90, photography=80, food=70, wellness=60, nightlife=20),
        pace="easy_going"), db_session)

    adventurous = run_planning_pipeline(_make_request(
        "friends", dict(adventure=95, nature=80, beaches=70, nightlife=75, photography=50),
        pace="packed"), db_session)

    relaxed_names = {a.name for d in relaxed.days for a in d.activities}
    adventurous_names = {a.name for d in adventurous.days for a in d.activities}
    assert relaxed_names != adventurous_names


def test_budget_too_low_reports_infeasibility_rather_than_silently_exceeding(db_session):
    # Section 35 -- Case: Budget too low
    req = _make_request("family", dict(culture=70, food=80, nature=60, adventure=10),
                         pace="easy_going", budget_total=3000, hotel_comfort="luxury")
    plan = run_planning_pipeline(req, db_session)

    assert plan.feasible is False
    assert any("exceeds the supplied budget" in n for n in plan.feasibility_notes)


def test_no_duplicate_activities_across_the_full_itinerary(db_session):
    req = _make_request("solo", dict(culture=60, history=60, photography=70), pace="balanced")
    plan = run_planning_pipeline(req, db_session)

    all_names = [a.name for d in plan.days for a in d.activities]
    assert len(all_names) == len(set(all_names))