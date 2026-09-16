"""
Pydantic request/response schemas -- the API contract described in
MASTER_PROJECT.md Section 37.
"""
from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator

from ml.schema_constants import INTERESTS


class PreferenceWeights(BaseModel):
    """0-100 preference weights per interest. These are independent
    weights, not probabilities -- they are not required to sum to 100
    (Section 4, Step 3)."""
    food: int = Field(50, ge=0, le=100)
    culture: int = Field(50, ge=0, le=100)
    nature: int = Field(50, ge=0, le=100)
    beach: int = Field(50, ge=0, le=100)
    wellness: int = Field(50, ge=0, le=100)
    adventure: int = Field(50, ge=0, le=100)
    nightlife: int = Field(50, ge=0, le=100)
    shopping: int = Field(50, ge=0, le=100)
    history: int = Field(50, ge=0, le=100)
    photography: int = Field(50, ge=0, le=100)
    wildlife: int = Field(50, ge=0, le=100)
    spirituality: int = Field(50, ge=0, le=100)

    def as_dict(self) -> Dict[str, int]:
        return {i: getattr(self, i) for i in INTERESTS}


class TripRequest(BaseModel):
    origin_city: str
    destination: str = "Goa"
    start_date: date
    end_date: date
    nights: int = Field(..., ge=1, le=21)

    traveller_type: str = Field(..., pattern="^(solo|couple|family|friends|seniors)$")
    adults: int = Field(..., ge=1)
    children: int = Field(0, ge=0)
    seniors: int = Field(0, ge=0)

    preference_weights: PreferenceWeights

    pace: str = Field(..., pattern="^(easy_going|balanced|packed)$")

    budget_total: Optional[float] = Field(None, gt=0,
                                           description="Hard total trip budget for the whole party, if supplied")
    hotel_comfort: str = Field(..., pattern="^(budget|standard|premium|luxury)$")

    dietary_preference: str = Field("no_preference",
                                     pattern="^(vegetarian|vegan|jain|non_vegetarian|no_preference)$")
    mobility_need: str = Field("none", pattern="^(none|reduced_walking|wheelchair)$")
    preferred_transport: str = Field("balanced",
                                      pattern="^(lowest_cost|fastest|balanced|public_transport|taxi_private)$")

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        start = info.data.get("start_date")
        if start and v < start:
            raise ValueError("end_date must not be before start_date")
        return v


class ActivityItem(BaseModel):
    name: str
    category: str
    period: str  # morning/afternoon/evening
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: int
    cost: float
    zone: str
    why_selected: str
    assumptions: List[str] = []


class MealItem(BaseModel):
    name: str
    meal_type: str
    estimated_cost_per_person: float
    zone: str


class DayPlan(BaseModel):
    day_number: int
    date: date
    zone_focus: str
    activities: List[ActivityItem]
    meals: List[MealItem]
    travel_time_minutes: int
    estimated_day_cost: float
    day_summary: str
    assumptions: List[str] = []


class SelectedHotel(BaseModel):
    name: str
    comfort_level: str
    zone: str
    price_per_night: float
    total_stay_cost: float
    why_selected: str


class SelectedTransport(BaseModel):
    mode: str
    duration_minutes: int
    estimated_cost_per_person: float
    total_cost: float
    is_indicative: bool = True


class CostBreakdown(BaseModel):
    transport_total: float
    hotel_total: float
    activities_total: float
    meals_total: float
    local_transport_total: float
    grand_total: float
    per_person_estimate: float


class PlanResponse(BaseModel):
    request_summary: Dict
    feasible: bool
    feasibility_notes: List[str]
    transport: Optional[SelectedTransport]
    hotel: Optional[SelectedHotel]
    days: List[DayPlan]
    cost_breakdown: Optional[CostBreakdown]
    assumptions: List[str]
    planning_summary: str