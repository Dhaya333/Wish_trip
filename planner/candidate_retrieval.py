"""
Retrieves candidate POIs, hotels, restaurants, transport routes, and local
travel times from the database for a given trip request, and converts
SQLAlchemy rows into plain dicts so the ML scoring layer (ml/predict.py)
and optimizer (planner/optimizer.py) don't need to depend on the ORM.

This is a single-destination (Goa) dataset -- there is no `Destination`
table to filter by, so `destination_name` on these functions is currently
accepted for API-shape compatibility but not used to filter Zones/POIs.
"""
from typing import Dict, List

from sqlalchemy.orm import Session

from database.models import (
    Hotel, LocalTravelTime, POI, Restaurant, TransportRoute, Zone,
)

# Real dietary_support values in restaurants.csv are things like
# "veg_and_non_veg" / "veg_only" / "non_veg_only" -- exact vocabulary may
# vary. This is a best-effort, case-insensitive substring match; if
# nothing matches, callers fall back to returning all restaurants rather
# than an empty list.
DIETARY_MATCH_TERMS = {
    "vegetarian": ["veg_only", "veg_and_non_veg", "vegetarian"],
    "vegan": ["vegan"],
    "jain": ["jain"],
    "non_vegetarian": ["non_veg", "veg_and_non_veg"],
}


def _row_to_dict(obj) -> Dict:
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def get_zones(session: Session, destination_name: str = "Goa") -> List[Dict]:
    zones = session.query(Zone).all()
    return [_row_to_dict(z) for z in zones]


def get_pois(session: Session, destination_name: str = "Goa") -> List[Dict]:
    pois = session.query(POI).all()
    result = []
    for p in pois:
        d = _row_to_dict(p)
        d["zone_name"] = p.zone.zone_name if p.zone else ""
        result.append(d)
    return result


def get_hotels(session: Session, destination_name: str, comfort_level: str) -> List[Dict]:
    hotels = session.query(Hotel).filter(Hotel.comfort_level == comfort_level).all()
    if not hotels:
        # fall back to all comfort levels rather than returning nothing --
        # the optimizer/ML score will still weigh the comfort mismatch
        hotels = session.query(Hotel).all()
    return [{**_row_to_dict(h), "zone_name": h.zone.zone_name if h.zone else ""} for h in hotels]


def get_restaurants(session: Session, destination_name: str, dietary_preference: str) -> List[Dict]:
    restaurants = session.query(Restaurant).all()
    all_rows = [{**_row_to_dict(r), "zone_name": r.zone.zone_name if r.zone else ""}
                for r in restaurants]

    if dietary_preference == "no_preference" or dietary_preference not in DIETARY_MATCH_TERMS:
        return all_rows

    terms = DIETARY_MATCH_TERMS[dietary_preference]
    matched = [
        row for row in all_rows
        if any(t in str(row.get("dietary_support", "")).lower() for t in terms)
    ]
    return matched if matched else all_rows


def get_transport_routes(session: Session, origin_city: str, destination_city: str) -> List[Dict]:
    routes = (
        session.query(TransportRoute)
        .filter(TransportRoute.origin_city.ilike(origin_city))
        .filter(TransportRoute.destination.ilike(destination_city))
        .all()
    )
    return [_row_to_dict(r) for r in routes]


def get_local_travel_time(session: Session, origin_zone_id: str, destination_zone_id: str) -> Dict:
    row = (
        session.query(LocalTravelTime)
        .filter(LocalTravelTime.origin_zone == origin_zone_id)
        .filter(LocalTravelTime.destination_zone == destination_zone_id)
        .first()
    )
    if row is None:
        # no recorded route -- indicative placeholder, explicitly flagged
        return {"distance_km": None, "duration_minutes": 45, "estimated_cost": 500,
                "is_placeholder": True}
    return _row_to_dict(row)