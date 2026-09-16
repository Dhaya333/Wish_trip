"""
Builds the real training tables for POI and hotel suitability models by
joining the interaction files against traveller attributes and item
attributes (Section: real-data training pipeline).

Inputs (ml/raw/):
    travellers.csv        -- one row per traveller profile, has 'split'
    poi_interactions.csv  -- one row per (traveller, POI) pair, has
                              'synthetic_suitability_score' label + 'split'
    hotel_interactions.csv-- one row per (traveller, hotel) pair, same shape

Reference data (data/raw/):
    pois.csv, hotels.csv  -- item attributes (category, affinities, etc.)

The 'split' column already present in the interaction files is treated as
the authoritative train/test split -- we do NOT re-shuffle or re-split,
so results stay comparable across runs and across the poi/hotel models.

Usage:
    python -m ml.build_training_data
Writes:
    ml/raw/poi_training_table.csv
    ml/raw/hotel_training_table.csv
"""
import os

import pandas as pd

DATA_RAW = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
ML_RAW = os.path.join(os.path.dirname(__file__), "raw")

TRAVELLER_COLS = [
    "traveller_id", "traveller_type", "adults", "children", "seniors",
    "total_party_size", "pace", "budget_level", "hotel_comfort",
    "mobility_need", "dietary_preference", "preferred_transport",
    "food_preference", "culture_preference", "nature_preference",
    "beach_preference", "wellness_preference", "adventure_preference",
    "nightlife_preference", "shopping_preference", "history_preference",
    "photography_preference", "wildlife_preference", "spirituality_preference",
]

POI_ITEM_COLS = [
    "poi_id", "category", "typical_duration_minutes", "accessibility_score",
    "quality_score", "food_affinity", "culture_affinity", "nature_affinity",
    "beach_affinity", "wellness_affinity", "adventure_affinity",
    "nightlife_affinity", "shopping_affinity", "history_affinity",
    "photography_affinity", "wildlife_affinity", "spirituality_affinity",
]

HOTEL_ITEM_COLS = [
    "hotel_id", "comfort_level", "star_category", "quality_score",
    "price_per_night", "room_capacity", "accessibility_score",
]


def build_poi_training_table() -> pd.DataFrame:
    travellers = pd.read_csv(os.path.join(ML_RAW, "travellers.csv"))[TRAVELLER_COLS]
    interactions = pd.read_csv(os.path.join(ML_RAW, "poi_interactions.csv"))
    pois = pd.read_csv(os.path.join(DATA_RAW, "pois.csv"))[POI_ITEM_COLS]

    df = interactions.merge(travellers, on="traveller_id", how="left")
    df = df.merge(pois, on="poi_id", how="left", suffixes=("", "_poi"))
    return df


def build_hotel_training_table() -> pd.DataFrame:
    travellers = pd.read_csv(os.path.join(ML_RAW, "travellers.csv"))[TRAVELLER_COLS]
    interactions = pd.read_csv(os.path.join(ML_RAW, "hotel_interactions.csv"))
    hotels = pd.read_csv(os.path.join(DATA_RAW, "hotels.csv"))[HOTEL_ITEM_COLS]

    df = interactions.merge(travellers, on="traveller_id", how="left")
    df = df.merge(hotels, on="hotel_id", how="left", suffixes=("", "_hotel"))
    return df


def main():
    poi_table = build_poi_training_table()
    hotel_table = build_hotel_training_table()

    poi_out = os.path.join(ML_RAW, "poi_training_table.csv")
    hotel_out = os.path.join(ML_RAW, "hotel_training_table.csv")
    poi_table.to_csv(poi_out, index=False)
    hotel_table.to_csv(hotel_out, index=False)

    print(f"POI training table: {len(poi_table)} rows -> {poi_out}")
    print(f"  split counts: {poi_table['split'].value_counts().to_dict()}")
    print(f"Hotel training table: {len(hotel_table)} rows -> {hotel_out}")
    print(f"  split counts: {hotel_table['split'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()