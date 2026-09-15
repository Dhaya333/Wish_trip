"""
Validation for critical planning rules that must hold before any
optimisation is attempted (Section 18 hard constraints, Section 40
testing strategy).
"""
from dataclasses import dataclass, field
from datetime import date
from typing import List

from planner.schemas import TripRequest


@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str] = field(default_factory=list)


def validate_trip_request(req: TripRequest) -> ValidationResult:
    errors: List[str] = []

    if req.end_date < req.start_date:
        errors.append("end_date cannot be before start_date.")

    expected_nights = (req.end_date - req.start_date).days
    if expected_nights != req.nights:
        errors.append(
            f"nights ({req.nights}) does not match the {expected_nights} night(s) "
            f"implied by start_date/end_date."
        )

    if req.nights < 1:
        errors.append("A trip must be at least 1 night.")

    if req.traveller_type == "family" and req.children == 0 and req.adults < 2:
        # not a hard error, but flag as an inconsistency worth surfacing
        errors.append(
            "traveller_type is 'family' but no children were specified and only "
            "one adult is present -- please confirm party composition."
        )

    if req.traveller_type == "seniors" and req.seniors == 0:
        errors.append("traveller_type is 'seniors' but seniors count is 0.")

    total_party = req.adults + req.children + req.seniors
    if total_party < 1:
        errors.append("Party size must include at least one traveller.")

    if req.mobility_need == "wheelchair" and req.pace == "packed":
        # soft warning folded in as a note, not a hard failure
        errors.append(
            "NOTE: wheelchair mobility need combined with a 'packed' pace may "
            "significantly reduce feasible activity options; the optimiser will "
            "prioritise accessibility over density."
        )

    hard_errors = [e for e in errors if not e.startswith("NOTE")]
    return ValidationResult(is_valid=len(hard_errors) == 0, errors=errors)