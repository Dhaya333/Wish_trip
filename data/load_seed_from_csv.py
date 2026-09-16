"""
Loads data/raw/*.csv directly into the database using the models in
database/models.py. Replaces the old hand-written data/seed_data.py.

Expected files, all in data/raw/:
    zones.csv, pois.csv, hotels.csv, restaurants.csv,
    local_travel_times.csv, transport_routes.csv, seasonal_context.csv

Usage:
    python -m data.load_seed_from_csv
"""
import os

import pandas as pd
from sqlalchemy.orm import Session

from database.models import (
    Base, Hotel, LocalTravelTime, POI, Restaurant, SeasonalContext,
    TransportRoute, Zone,
)
import database.session as db_session

RAW_DIR = os.path.join(os.path.dirname(__file__), "raw")


def _read(filename: str) -> pd.DataFrame:
    path = os.path.join(RAW_DIR, filename)
    df = pd.read_csv(path)
    # normalise NaN -> None so SQLAlchemy inserts NULL instead of the float 'nan'
    return df.where(pd.notnull(df), None)


def _bool_cols(df: pd.DataFrame, cols):
    for c in cols:
        if c in df.columns:
            df[c] = df[c].astype(int).astype(bool)
    return df


def load_zones(session: Session):
    df = _read("zones.csv")
    session.bulk_insert_mappings(Zone, df.to_dict(orient="records"))
    return len(df)


def load_pois(session: Session):
    df = _read("pois.csv")
    session.bulk_insert_mappings(POI, df.to_dict(orient="records"))
    return len(df)


def load_hotels(session: Session):
    df = _read("hotels.csv")
    df = _bool_cols(df, ["breakfast", "pool", "parking", "beach_access",
                          "family_facilities", "wellness", "restaurant", "wifi"])
    session.bulk_insert_mappings(Hotel, df.to_dict(orient="records"))
    return len(df)


def load_restaurants(session: Session):
    df = _read("restaurants.csv")
    df = _bool_cols(df, ["breakfast_support", "lunch_support", "dinner_support"])
    session.bulk_insert_mappings(Restaurant, df.to_dict(orient="records"))
    return len(df)


def load_local_travel_times(session: Session):
    df = _read("local_travel_times.csv")
    df = df.rename(columns={"origin_zone": "origin_zone", "destination_zone": "destination_zone"})
    session.bulk_insert_mappings(LocalTravelTime, df.to_dict(orient="records"))
    return len(df)


def load_transport_routes(session: Session):
    df = _read("transport_routes.csv")
    session.bulk_insert_mappings(TransportRoute, df.to_dict(orient="records"))
    return len(df)


def load_seasonal_context(session: Session):
    df = _read("seasonal_context.csv")
    session.bulk_insert_mappings(SeasonalContext, df.to_dict(orient="records"))
    return len(df)


def reset_and_seed():
    # Read engine/SessionLocal from the module (not via a top-level
    # `from ... import`) so callers -- e.g. the test suite -- can swap in a
    # different engine/session at runtime before calling this function.
    engine = db_session.engine
    SessionLocal = db_session.SessionLocal

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        n_zones = load_zones(session)
        session.flush()
        n_pois = load_pois(session)
        n_hotels = load_hotels(session)
        n_restaurants = load_restaurants(session)
        session.flush()
        n_travel = load_local_travel_times(session)
        n_transport = load_transport_routes(session)
        n_seasonal = load_seasonal_context(session)

        session.commit()
        print(f"Loaded {n_zones} zones, {n_pois} POIs, {n_hotels} hotels, "
              f"{n_restaurants} restaurants, {n_travel} local travel-time rows, "
              f"{n_transport} transport routes, {n_seasonal} seasonal context rows.")
    finally:
        session.close()


if __name__ == "__main__":
    reset_and_seed()