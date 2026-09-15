"""
SQLAlchemy ORM models implementing the data model described in
MASTER_PROJECT.md Section 28 (Data Model).

Every record that is not derived from verified public information carries
an explicit `is_synthetic_or_estimated` / assumption flag, per Section 30
(Data Quality Rules). Nothing here should be presented to the end user as
a verified real-time fact.
"""
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Destination(Base):
    __tablename__ = "destinations"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False, unique=True)
    state = Column(String(120), nullable=False)
    country = Column(String(120), nullable=False, default="India")

    zones = relationship("Zone", back_populates="destination")


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True)
    destination_id = Column(Integer, ForeignKey("destinations.id"), nullable=False)
    name = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    destination = relationship("Destination", back_populates="zones")
    pois = relationship("POI", back_populates="zone")
    hotels = relationship("Hotel", back_populates="zone")
    restaurants = relationship("Restaurant", back_populates="zone")


class POI(Base):
    """A point of interest / activity."""
    __tablename__ = "pois"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(160), nullable=False)
    category = Column(String(60), nullable=False)
    description = Column(Text, default="")

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    duration_minutes = Column(Integer, nullable=False)
    cost = Column(Float, nullable=False, default=0.0)

    opening_time = Column(String(5), nullable=True)   # "HH:MM", None if unknown
    closing_time = Column(String(5), nullable=True)
    opening_hours_is_assumption = Column(Boolean, default=False)

    seasonality_note = Column(String(200), default="")
    accessibility_level = Column(String(20), default="unknown")  # low/medium/high

    family_suitability = Column(Integer, default=50)   # 0-100
    senior_suitability = Column(Integer, default=50)
    solo_suitability = Column(Integer, default=50)
    couple_suitability = Column(Integer, default=50)
    friends_suitability = Column(Integer, default=50)

    morning_suitability = Column(Integer, default=50)
    afternoon_suitability = Column(Integer, default=50)
    evening_suitability = Column(Integer, default=50)

    # Interest affinity fields (Section 8 taxonomy), 0-100 each
    affinity_food = Column(Integer, default=0)
    affinity_culture = Column(Integer, default=0)
    affinity_nature = Column(Integer, default=0)
    affinity_beaches = Column(Integer, default=0)
    affinity_wellness = Column(Integer, default=0)
    affinity_adventure = Column(Integer, default=0)
    affinity_nightlife = Column(Integer, default=0)
    affinity_shopping = Column(Integer, default=0)
    affinity_history = Column(Integer, default=0)
    affinity_photography = Column(Integer, default=0)
    affinity_wildlife = Column(Integer, default=0)
    affinity_spirituality = Column(Integer, default=0)

    popularity_proxy = Column(Integer, default=50)  # 0-100, curated quality/popularity proxy

    is_synthetic_or_estimated = Column(Boolean, default=False)
    source_note = Column(String(200), default="curated public information")

    zone = relationship("Zone", back_populates="pois")


class Hotel(Base):
    __tablename__ = "hotels"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(160), nullable=False)
    comfort_level = Column(String(20), nullable=False)  # budget/standard/premium/luxury

    price_per_night = Column(Float, nullable=False)
    room_capacity = Column(Integer, default=2)
    amenities = Column(String(300), default="")

    accessibility_level = Column(String(20), default="unknown")
    family_suitability = Column(Integer, default=50)
    senior_suitability = Column(Integer, default=50)
    solo_suitability = Column(Integer, default=50)
    couple_suitability = Column(Integer, default=50)
    friends_suitability = Column(Integer, default=50)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    popularity_proxy = Column(Integer, default=50)

    is_synthetic_or_estimated = Column(Boolean, default=True)
    source_note = Column(String(200), default="indicative/estimated price")

    zone = relationship("Zone", back_populates="hotels")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(Integer, primary_key=True)
    zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    name = Column(String(160), nullable=False)
    cuisine = Column(String(120), default="")
    meal_types = Column(String(60), default="lunch,dinner")  # comma separated
    dietary_support = Column(String(120), default="non_vegetarian,vegetarian")

    price_level = Column(String(20), default="mid")  # low/mid/high
    average_cost_per_person = Column(Float, nullable=False)

    opening_time = Column(String(5), default="11:00")
    closing_time = Column(String(5), default="23:00")

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    suitable_party_types = Column(String(120), default="solo,couple,family,friends,seniors")

    is_synthetic_or_estimated = Column(Boolean, default=True)

    zone = relationship("Zone", back_populates="restaurants")


class TransportRoute(Base):
    """Intercity transport, origin city -> destination (and return)."""
    __tablename__ = "transport_routes"

    id = Column(Integer, primary_key=True)
    origin_city = Column(String(120), nullable=False)
    destination_city = Column(String(120), nullable=False)
    mode = Column(String(20), nullable=False)  # flight/train/bus/car

    departure_window = Column(String(40), default="")
    arrival_window = Column(String(40), default="")
    duration_minutes = Column(Integer, nullable=False)
    estimated_cost_per_person = Column(Float, nullable=False)
    transfers = Column(Integer, default=0)
    comfort_level = Column(String(20), default="standard")
    party_capacity_assumption = Column(String(120), default="")

    is_indicative = Column(Boolean, default=True)


class LocalTravelTime(Base):
    """Zone-to-zone local travel time/cost matrix within the destination."""
    __tablename__ = "local_travel_times"

    id = Column(Integer, primary_key=True)
    origin_zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    destination_zone_id = Column(Integer, ForeignKey("zones.id"), nullable=False)
    mode = Column(String(20), nullable=False, default="taxi")

    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    estimated_cost = Column(Float, nullable=False)

    is_indicative = Column(Boolean, default=True)


class SeasonContext(Base):
    __tablename__ = "season_context"

    id = Column(Integer, primary_key=True)
    month = Column(Integer, nullable=False)  # 1-12
    poi_id = Column(Integer, ForeignKey("pois.id"), nullable=False)
    suitability_modifier = Column(Integer, default=0)  # -100..+100
    context_note = Column(String(200), default="")
    confidence = Column(String(20), default="low")  # low/medium/high


class PlanRequestLog(Base):
    """Optional persisted record of a planning request/response for audit."""
    __tablename__ = "plan_request_log"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    request_json = Column(Text, nullable=False)
    response_json = Column(Text, nullable=False)
    feasible = Column(Boolean, default=True)