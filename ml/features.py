"""
Feature construction shared between training and inference, so the
candidate-scoring path at planning time uses exactly the same feature
definitions the models were trained on (Section 11-13).
"""
from typing import Dict, List

from ml.synthetic_data import INTERESTS

CATEGORICAL_COLS = ["traveller_type", "budget_level", "pace", "mobility_need",
                     "item_accessibility"]
NUMERIC_COLS_BASE = ["adults", "children", "seniors", "item_cost", "item_duration",
                      "item_popularity", "item_party_suit"]


def poi_feature_columns() -> List[str]:
    return CATEGORICAL_COLS + NUMERIC_COLS_BASE + \
        [f"pref_{i}" for i in INTERESTS] + [f"affinity_{i}" for i in INTERESTS]


def hotel_feature_columns() -> List[str]:
    # hotels don't carry interest affinities in this V1 data model
    return CATEGORICAL_COLS + NUMERIC_COLS_BASE + [f"pref_{i}" for i in INTERESTS]


def build_inference_row(traveller: dict, item: dict, is_hotel: bool = False) -> Dict:
    """
    Builds one feature row for a single (traveller, candidate item) pair at
    planning time, mirroring generate_training_rows() in ml/synthetic_data.py.
    `traveller` is expected to have: traveller_type, adults, children, seniors,
    budget_level, pace, mobility_need, preferences (dict of interest->0-100).
    """
    row = {
        "traveller_type": traveller["traveller_type"],
        "adults": traveller["adults"],
        "children": traveller["children"],
        "seniors": traveller["seniors"],
        "budget_level": traveller["budget_level"],
        "pace": traveller["pace"],
        "mobility_need": traveller["mobility_need"],
        "item_cost": item.get("cost", item.get("price_per_night", 0)),
        "item_duration": item.get("duration_minutes", 0),
        "item_popularity": item.get("popularity_proxy", 50),
        "item_accessibility": item.get("accessibility_level", "unknown"),
        "item_party_suit": item.get(f"{traveller['traveller_type']}_suitability", 50),
    }
    for i in INTERESTS:
        row[f"pref_{i}"] = traveller["preferences"].get(i, 0)
    if not is_hotel:
        for i in INTERESTS:
            row[f"affinity_{i}"] = item.get(f"affinity_{i}", 0)
    return row