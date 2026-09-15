"""
Retrieves candidate POIs, hotels, restaurants, transport routes, and local
travel times from the database for a given trip request, and converts
SQLAlchemy rows into plain dicts so the ML scoring layer (ml/predict.py)
and optimizer (planner/optimizer.py) don't need to depend on the ORM.
"""
from typing import Dict, List

from sqlalchemy.orm import Session

from database.models import (
    Hotel, LocalTravelTime, POI, Restaurant, TransportRoute, Zone,
)


def _row_to_dict(obj) -> Dict:
    d = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
    return d


def get_zones(session: Session, destination_name: str) -> List[Dict]:
    zones = (
        session.query(Zone)
        .join(Zone.destination)
        .filter(Zone.destination.has(name=destination_name))
        .all()
    )
    return [_row_to_dict(z) for z in zones]


def get_pois(session: Session, destination_name: str) -> List[Dict]:
    pois = (
        session.query(POI)
        .join(POI.zone)
        .join(Zone.destination)
        .filter(Zone.destination.has(name=destination_name))
        .all()
    )
    result = []
    for p in pois:
        d = _row_to_dict(p)
        d["zone_name"] = p.zone.name
        result.append(d)
    return result


def get_hotels(session: Session, destination_name: str, comfort_level: str) -> List[Dict]:
    hotels = (
        session.query(Hotel)
        .join(Hotel.zone)
        .join(Zone.destination)
        .filter(Zone.destination.has(name=destination_name))
        .filter(Hotel.comfort_level == comfort_level)
        .all()
    )
    if not hotels:
        # fall back to all comfort levels rather than returning nothing --
        # the optimizer will still weigh comfort mismatch via the ML score
        hotels = (
            session.query(Hotel)
            .join(Hotel.zone)
            .join(Zone.destination)
            .filter(Zone.destination.has(name=destination_name))
            .all()
        )
    result = []
    for h in hotels:
        d = _row_to_dict(h)
        d["zone_name"] = h.zone.name
        result.append(d)
    return result


def get_restaurants(session: Session, destination_name: str, dietary_preference: str) -> List[Dict]:
    restaurants = (
        session.query(Restaurant)
        .join(Restaurant.zone)
        .join(Zone.destination)
        .filter(Zone.destination.has(name=destination_name))
        .all()
    )
    result = []
    for r in restaurants:
        d = _row_to_dict(r)
        d["zone_name"] = r.zone.name
        if dietary_preference != "no_preference" and dietary_preference not in d["dietary_support"]:
            continue
        result.append(d)
    return result if result else [
        {**_row_to_dict(r), "zone_name": r.zone.name} for r in restaurants
    ]


def get_transport_routes(session: Session, origin_city: str, destination_city: str) -> List[Dict]:
    routes = (
        session.query(TransportRoute)
        .filter(TransportRoute.origin_city.ilike(origin_city))
        .filter(TransportRoute.destination_city.ilike(destination_city))
        .all()
    )
    return [_row_to_dict(r) for r in routes]


def get_local_travel_time(session: Session, origin_zone_id: int, destination_zone_id: int) -> Dict:
    row = (
        session.query(LocalTravelTime)
        .filter(LocalTravelTime.origin_zone_id == origin_zone_id)
        .filter(LocalTravelTime.destination_zone_id == destination_zone_id)
        .first()
    )
    if row is None:
        # no recorded route -- indicative placeholder, explicitly flagged
        return {"distance_km": None, "duration_minutes": 45, "estimated_cost": 500,
                "is_indicative": True, "is_placeholder": True}
    return _row_to_dict(row)