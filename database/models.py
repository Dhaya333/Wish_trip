"""
SQLAlchemy ORM models matching the real Goa dataset columns
(data/raw/*.csv). Natural string IDs from the CSVs (Z01, POI0001, H0001,
R0001) are used directly as primary keys so joins against the CSVs never
need an id-remapping step.

ml/raw/*.csv (travellers, poi_interactions, hotel_interactions) are NOT
loaded into this database -- they're training data only, consumed
directly by ml/build_training_data.py via pandas.
"""
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(String(10), primary_key=True)       # e.g. "Z01"
    zone_name = Column(String(120), nullable=False)
    region = Column(String(120), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    pois = relationship("POI", back_populates="zone")
    hotels = relationship("Hotel", back_populates="zone")
    restaurants = relationship("Restaurant", back_populates="zone")


class POI(Base):
    __tablename__ = "pois"

    poi_id = Column(String(12), primary_key=True)         
    name = Column(String(160), nullable=False)
    zone_id = Column(String(10), ForeignKey("zones.zone_id"), nullable=False)
    category = Column(String(60), nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    typical_duration_minutes = Column(Integer, nullable=False)
    opening_time = Column(String(5), nullable=True)
    closing_time = Column(String(5), nullable=True)

    morning_score = Column(Integer, default=50)
    afternoon_score = Column(Integer, default=50)
    evening_score = Column(Integer, default=50)

    base_cost = Column(Float, default=0.0)
    child_cost = Column(Float, default=0.0)
    senior_cost = Column(Float, default=0.0)

    solo_suitability = Column(Integer, default=50)
    couple_suitability = Column(Integer, default=50)
    family_suitability = Column(Integer, default=50)
    friends_suitability = Column(Integer, default=50)
    senior_suitability = Column(Integer, default=50)
    child_suitability = Column(Integer, default=50)

    accessibility_score = Column(Integer, default=50)
    quality_score = Column(Float, default=50.0)

    food_affinity = Column(Integer, default=0)
    culture_affinity = Column(Integer, default=0)
    nature_affinity = Column(Integer, default=0)
    beach_affinity = Column(Integer, default=0)
    wellness_affinity = Column(Integer, default=0)
    adventure_affinity = Column(Integer, default=0)
    nightlife_affinity = Column(Integer, default=0)
    shopping_affinity = Column(Integer, default=0)
    history_affinity = Column(Integer, default=0)
    photography_affinity = Column(Integer, default=0)
    wildlife_affinity = Column(Integer, default=0)
    spirituality_affinity = Column(Integer, default=0)

    zone = relationship("Zone", back_populates="pois")
    seasonal_context = relationship("SeasonalContext", back_populates="poi")


class Hotel(Base):
    __tablename__ = "hotels"

    hotel_id = Column(String(12), primary_key=True)       # e.g. "H0001"
    name = Column(String(160), nullable=False)
    zone_id = Column(String(10), ForeignKey("zones.zone_id"), nullable=False)
    comfort_level = Column(String(20), nullable=False)    # budget/standard/premium/luxury
    star_category = Column(Integer, default=3)
    quality_score = Column(Float, default=50.0)

    price_per_night = Column(Float, nullable=False)
    room_capacity = Column(Integer, default=2)
    estimated_extra_guest_cost = Column(Float, default=0.0)

    solo_score = Column(Integer, default=50)
    couple_score = Column(Integer, default=50)
    family_score = Column(Integer, default=50)
    friends_score = Column(Integer, default=50)
    senior_score = Column(Integer, default=50)
    child_score = Column(Integer, default=50)
    accessibility_score = Column(Integer, default=50)

    breakfast = Column(Boolean, default=False)
    pool = Column(Boolean, default=False)
    parking = Column(Boolean, default=False)
    beach_access = Column(Boolean, default=False)
    family_facilities = Column(Boolean, default=False)
    wellness = Column(Boolean, default=False)
    restaurant = Column(Boolean, default=False)
    wifi = Column(Boolean, default=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_to_major_poi_clusters_km = Column(Float, default=0.0)
    average_access_travel_time_min = Column(Float, default=0.0)

    zone = relationship("Zone", back_populates="hotels")


class Restaurant(Base):
    __tablename__ = "restaurants"

    restaurant_id = Column(String(12), primary_key=True)  # e.g. "R0001"
    name = Column(String(160), nullable=False)
    zone_id = Column(String(10), ForeignKey("zones.zone_id"), nullable=False)
    cuisine = Column(String(120), default="")
    meal_types = Column(String(60), default="")           # e.g. "breakfast;lunch;dinner"
    dietary_support = Column(String(60), default="")       # e.g. "veg_and_non_veg"
    price_level = Column(String(20), default="mid")
    average_meal_cost = Column(Float, nullable=False)

    breakfast_support = Column(Boolean, default=False)
    lunch_support = Column(Boolean, default=False)
    dinner_support = Column(Boolean, default=False)
    opening_period = Column(String(20), default="")        # e.g. "07:00-23:00"

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    zone = relationship("Zone", back_populates="restaurants")


class LocalTravelTime(Base):
    __tablename__ = "local_travel_times"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_zone = Column(String(10), ForeignKey("zones.zone_id"), nullable=False)
    destination_zone = Column(String(10), ForeignKey("zones.zone_id"), nullable=False)
    mode = Column(String(20), nullable=False)              # walking/scooter/taxi/...

    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    estimated_cost = Column(Float, nullable=False)
    comfort = Column(Integer, default=50)
    accessibility = Column(Integer, default=50)


class TransportRoute(Base):
    __tablename__ = "transport_routes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    origin_city = Column(String(120), nullable=False)
    destination = Column(String(120), nullable=False)
    mode = Column(String(20), nullable=False)              # flight/train/bus

    departure_window = Column(String(20), default="")      # morning/evening/...
    arrival_window = Column(String(20), default="")
    duration_minutes = Column(Float, nullable=False)
    estimated_cost_per_person = Column(Float, nullable=False)
    transfer_count = Column(Integer, default=0)
    comfort_score = Column(Integer, default=50)
    availability_status_type = Column(String(20), default="")   # limited/seasonal/frequent
    source_status = Column(String(30), default="synthetic_indicative")


class SeasonalContext(Base):
    __tablename__ = "seasonal_context"

    id = Column(Integer, primary_key=True, autoincrement=True)
    poi_id = Column(String(12), ForeignKey("pois.poi_id"), nullable=False)
    month = Column(String(20), nullable=False)
    season = Column(String(30), nullable=False)
    seasonal_suitability = Column(Integer, default=50)
    morning_modifier = Column(Integer, default=0)
    afternoon_modifier = Column(Integer, default=0)
    evening_modifier = Column(Integer, default=0)
    weather_risk_proxy = Column(String(20), default="low")
    season_note = Column(Text, default="")
    confidence = Column(String(20), default="low")

    poi = relationship("POI", back_populates="seasonal_context")