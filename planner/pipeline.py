"""
Orchestrates the full planning pipeline end-to-end :

    Validate -> Retrieve candidates -> ML score -> Select hotel ->
    Optimise days -> Validate feasibility -> Generate explanations ->
    Assemble structured itinerary
"""
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ml.predict import score_hotels, score_pois
from planner.candidate_retrieval import (
    get_hotels, get_local_travel_time, get_pois, get_restaurants,
    get_transport_routes, get_zones,
)
from planner.explanations import day_summary, explain_activity, explain_hotel
from planner.optimizer import ScoredCandidate, build_day_plans, select_hotel
from planner.schemas import (
    ActivityItem, CostBreakdown, DayPlan, MealItem, PlanResponse,
    SelectedHotel, SelectedTransport, TripRequest,
)
from planner.validators import validate_trip_request

BUDGET_LEVEL_THRESHOLDS = [(15000, "low"), (40000, "medium")]  # else "high"


def _infer_budget_level(budget_total: Optional[float], party_size: int) -> str:
    if budget_total is None:
        return "medium"
    per_person = budget_total / max(party_size, 1)
    for threshold, level in BUDGET_LEVEL_THRESHOLDS:
        if per_person <= threshold:
            return level
    return "high"


def _traveller_dict(req: TripRequest) -> Dict:
    return {
        "traveller_type": req.traveller_type,
        "adults": req.adults,
        "children": req.children,
        "seniors": req.seniors,
        "budget_level": _infer_budget_level(req.budget_total, req.adults + req.children + req.seniors),
        "pace": req.pace,
        "mobility_need": req.mobility_need,
        "preferences": req.preference_weights.as_dict(),
    }


def _pick_best_meal(restaurants: List[Dict], meal_type: str, dietary_preference: str) -> Optional[Dict]:
    candidates = [r for r in restaurants if meal_type in r.get("meal_types", "")]
    if dietary_preference != "no_preference":
        pref_matched = [r for r in candidates if dietary_preference in r.get("dietary_support", "")]
        if pref_matched:
            candidates = pref_matched
    if not candidates:
        return None
    return min(candidates, key=lambda r: r["average_meal_cost"])


def run_planning_pipeline(req: TripRequest, session: Session) -> PlanResponse:
    validation = validate_trip_request(req)
    hard_notes = [e for e in validation.errors if not e.startswith("NOTE")]
    soft_notes = [e[len("NOTE: "):] for e in validation.errors if e.startswith("NOTE")]

    if not validation.is_valid:
        return PlanResponse(
            request_summary=req.model_dump(mode="json"),
            feasible=False,
            feasibility_notes=hard_notes,
            transport=None, hotel=None, days=[], cost_breakdown=None,
            assumptions=soft_notes,
            planning_summary="The trip request could not be validated; see feasibility_notes.",
        )

    traveller = _traveller_dict(req)
    party_size = req.adults + req.children + req.seniors
    assumptions: List[str] = list(soft_notes)
    feasibility_notes: List[str] = []

    # ---- Transport ----
    routes = get_transport_routes(session, req.origin_city, req.destination)
    selected_transport = None
    transport_cost_total = 0.0
    if routes:
        def _transport_key(r):
            if req.preferred_transport == "lowest_cost":
                return r["estimated_cost_per_person"]
            if req.preferred_transport == "fastest":
                return r["duration_minutes"]
            return r["estimated_cost_per_person"] * 0.5 + r["duration_minutes"] * 0.5

        best_route = min(routes, key=_transport_key)
        transport_cost_total = best_route["estimated_cost_per_person"] * party_size * 2  # round trip
        selected_transport = SelectedTransport(
            mode=best_route["mode"], duration_minutes=best_route["duration_minutes"],
            estimated_cost_per_person=best_route["estimated_cost_per_person"],
            total_cost=transport_cost_total, is_indicative=True,
        )
        assumptions.append("Intercity transport cost/duration is indicative and not sourced from a live booking API.")
    else:
        feasibility_notes.append(f"No transport route data available for {req.origin_city} -> {req.destination}.")

    # ---- Hotel ----
    hotel_candidates = get_hotels(session, req.destination, req.hotel_comfort)
    hotel_scores = score_hotels(traveller, hotel_candidates)
    scored_hotels = list(zip(hotel_candidates, hotel_scores))

    remaining_budget = None
    if req.budget_total is not None:
        remaining_budget = req.budget_total - transport_cost_total
    hotel_budget_cap = remaining_budget * 0.4 if remaining_budget is not None else None

    chosen_hotel, hotel_notes = select_hotel(scored_hotels, req.nights, hotel_budget_cap)
    feasibility_notes.extend(hotel_notes)

    selected_hotel = None
    hotel_total_cost = 0.0
    if chosen_hotel is not None:
        hotel_total_cost = chosen_hotel["price_per_night"] * req.nights
        selected_hotel = SelectedHotel(
            name=chosen_hotel["name"], comfort_level=chosen_hotel["comfort_level"],
            zone=chosen_hotel["zone_name"], price_per_night=chosen_hotel["price_per_night"],
            total_stay_cost=hotel_total_cost,
            why_selected=explain_hotel(chosen_hotel, req.hotel_comfort, req.traveller_type,
                                        budget_constrained=bool(hotel_notes)),
        )
        assumptions.append("Hotel pricing is indicative/estimated, not a live rate.")

    # ---- Activities ----
    pois = get_pois(session, req.destination)
    poi_scores = score_pois(traveller, pois)
    zone_lookup = {z["zone_id"]: z["zone_name"] for z in get_zones(session, req.destination)}
    scored_candidates = [ScoredCandidate(poi=p, ml_score=s, zone_id=p["zone_id"])
                          for p, s in zip(pois, poi_scores)]

    per_day_activity_budget = None
    if remaining_budget is not None:
        leftover_for_activities_meals = max(remaining_budget - hotel_total_cost, 0)
        per_day_activity_budget = leftover_for_activities_meals / max(req.nights, 1) * 0.6

    day_results, day_notes = build_day_plans(
        candidates=scored_candidates, n_days=req.nights, pace=req.pace,
        traveller_type=req.traveller_type, mobility_need=req.mobility_need,
        per_day_soft_budget=per_day_activity_budget, zone_name_lookup=zone_lookup,
    )
    feasibility_notes.extend(day_notes)

    restaurants = get_restaurants(session, req.destination, req.dietary_preference)

    days: List[DayPlan] = []
    activities_total = 0.0
    meals_total = 0.0
    local_transport_total = 0.0

    for idx, day in enumerate(day_results):
        activity_items = []
        activity_names_for_summary = []
        for sched in day.scheduled:
            poi = sched["poi"]
            explanation = explain_activity(poi, traveller["preferences"], sched["period"], req.traveller_type)
            activity_items.append(ActivityItem(
                name=poi["name"], category=poi["category"], period=sched["period"],
                start_time=sched["start_time"], end_time=None,
                duration_minutes=sched["duration_minutes"], cost=poi.get("base_cost", 0),
                zone=poi.get("zone_name", zone_lookup.get(poi.get("zone_id"), "")),
                why_selected=explanation, assumptions=sched["assumptions"],
            ))
            activity_names_for_summary.append(poi["name"])
            activities_total += poi.get("base_cost", 0)

        lunch = _pick_best_meal(restaurants, "lunch", req.dietary_preference)
        dinner = _pick_best_meal(restaurants, "dinner", req.dietary_preference)
        meal_items = []
        for meal, meal_type in ((lunch, "lunch"), (dinner, "dinner")):
            if meal:
                cost = meal["average_meal_cost"] * party_size
                meal_items.append(MealItem(name=meal["name"], meal_type=meal_type,
                                            estimated_cost_per_person=meal["average_meal_cost"],
                                            zone=meal["zone_name"]))
                meals_total += cost

        travel_minutes = 30 * max(len(day.scheduled) - 1, 0)  # simple indicative inter-stop estimate
        local_cost_estimate = 150 * max(len(day.scheduled), 1)
        local_transport_total += local_cost_estimate

        days.append(DayPlan(
            day_number=day.day_number,
            date=req.start_date if idx == 0 else req.start_date.fromordinal(req.start_date.toordinal() + idx),
            zone_focus=day.zone_focus_name or "Unassigned",
            activities=activity_items,
            meals=meal_items,
            travel_time_minutes=travel_minutes,
            estimated_day_cost=day.day_cost + local_cost_estimate,
            day_summary=day_summary(activity_names_for_summary, day.zone_focus_name or "Goa", req.pace),
            assumptions=["Local travel time/cost between stops is an indicative estimate."],
        ))

    grand_total = transport_cost_total + hotel_total_cost + activities_total + meals_total + local_transport_total
    budget_exceeded = req.budget_total is not None and grand_total > req.budget_total
    if budget_exceeded:
        feasibility_notes.append(
            f"Estimated total cost (INR {grand_total:,.0f}) exceeds the supplied budget "
            f"(INR {req.budget_total:,.0f}). This is the closest feasible plan found; "
            f"consider a lower comfort level, shorter trip, or reduced activity density."
        )

    cost_breakdown = CostBreakdown(
        transport_total=transport_cost_total, hotel_total=hotel_total_cost,
        activities_total=activities_total, meals_total=meals_total,
        local_transport_total=local_transport_total, grand_total=grand_total,
        per_person_estimate=grand_total / max(party_size, 1),
    )

    feasible = len(feasibility_notes) == 0 or not budget_exceeded
    # a plan is still returned even when infeasible (Section 35), with notes explaining why

    return PlanResponse(
        request_summary=req.model_dump(mode="json"),
        feasible=not budget_exceeded,
        feasibility_notes=feasibility_notes,
        transport=selected_transport,
        hotel=selected_hotel,
        days=days,
        cost_breakdown=cost_breakdown,
        assumptions=sorted(set(assumptions)),
        planning_summary=(
            f"{req.nights}-night {req.pace.replace('_', '-')} {req.traveller_type} trip to {req.destination} "
            f"with {selected_hotel.comfort_level if selected_hotel else 'no'} hotel comfort, "
            f"estimated total cost INR {grand_total:,.0f}."
        ),
    )