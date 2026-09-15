"""
Tests for planner/validators.py -- date/nights/budget validation
(Section 40 testing strategy).
"""
from datetime import date

import pytest

from planner.schemas import PreferenceWeights, TripRequest
from planner.validators import validate_trip_request


def _base_request(**overrides) -> TripRequest:
    defaults = dict(
        origin_city="Mumbai",
        destination="Goa",
        start_date=date(2026, 12, 10),
        end_date=date(2026, 12, 14),
        nights=4,
        traveller_type="couple",
        adults=2,
        children=0,
        seniors=0,
        preference_weights=PreferenceWeights(),
        pace="balanced",
        budget_total=60000,
        hotel_comfort="standard",
        dietary_preference="no_preference",
        mobility_need="none",
        preferred_transport="balanced",
    )
    defaults.update(overrides)
    return TripRequest(**defaults)


def test_valid_request_passes():
    req = _base_request()
    result = validate_trip_request(req)
    assert result.is_valid
    assert not [e for e in result.errors if not e.startswith("NOTE")]


def test_nights_mismatch_is_rejected():
    req = _base_request(nights=2)  # actual span is 4 nights
    result = validate_trip_request(req)
    assert not result.is_valid
    assert any("does not match" in e for e in result.errors)


def test_end_date_before_start_date_is_rejected():
    # Pydantic's own field_validator should already reject this at
    # construction time, before validate_trip_request is even reached.
    with pytest.raises(ValueError):
        _base_request(start_date=date(2026, 12, 14), end_date=date(2026, 12, 10), nights=4)


def test_seniors_traveller_type_without_seniors_is_rejected():
    req = _base_request(traveller_type="seniors", adults=1, seniors=0)
    result = validate_trip_request(req)
    assert not result.is_valid
    assert any("seniors count is 0" in e for e in result.errors)


def test_wheelchair_plus_packed_pace_is_a_soft_note_not_a_hard_failure():
    req = _base_request(mobility_need="wheelchair", pace="packed")
    result = validate_trip_request(req)
    assert result.is_valid  # soft NOTE only, not a hard error
    assert any(e.startswith("NOTE") for e in result.errors)