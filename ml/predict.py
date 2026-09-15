"""
Inference-time scoring for POIs and hotels.

Tries to load a trained CatBoost model (produced by ml/train_poi_model.py
/ ml/train_hotel_model.py). If no trained model artifact is present, falls
back to the transparent rule-based utility function from
ml/synthetic_data.py -- this is Baseline 2 in Section 33, and it keeps the
planner usable even before any training run has happened.

The planner (planner/candidate_retrieval.py + planner/optimizer.py) only
calls the functions in this module -- it never needs to know whether a
CatBoost model or the rule-based fallback produced the score.
"""
import os
from typing import Dict, List

import pandas as pd

from ml.features import CATEGORICAL_COLS, build_inference_row, hotel_feature_columns, poi_feature_columns
from ml.synthetic_data import SyntheticProfile, utility_score

POI_MODEL_PATH = "models/poi_model.cbm"
HOTEL_MODEL_PATH = "models/hotel_model.cbm"

_poi_model = None
_hotel_model = None
_catboost_import_failed = False


def _try_load_catboost_model(path: str):
    global _catboost_import_failed
    if not os.path.exists(path):
        return None
    try:
        from catboost import CatBoostRegressor
        model = CatBoostRegressor()
        model.load_model(path)
        return model
    except Exception:
        _catboost_import_failed = True
        return None


def _get_poi_model():
    global _poi_model
    if _poi_model is None:
        _poi_model = _try_load_catboost_model(POI_MODEL_PATH)
    return _poi_model


def _get_hotel_model():
    global _hotel_model
    if _hotel_model is None:
        _hotel_model = _try_load_catboost_model(HOTEL_MODEL_PATH)
    return _hotel_model


def _traveller_to_profile(traveller: dict) -> SyntheticProfile:
    return SyntheticProfile(
        traveller_type=traveller["traveller_type"],
        adults=traveller["adults"],
        children=traveller["children"],
        seniors=traveller["seniors"],
        budget_level=traveller["budget_level"],
        pace=traveller["pace"],
        mobility_need=traveller["mobility_need"],
        preferences=traveller["preferences"],
    )


def score_items(traveller: dict, items: List[dict], is_hotel: bool = False) -> List[float]:
    """
    Returns a suitability score (0-100) per item, in the same order as
    `items`. Uses the trained CatBoost model when available, otherwise the
    rule-based utility function (Section 33, Baseline 2).
    """
    model = _get_hotel_model() if is_hotel else _get_poi_model()

    if model is not None:
        cols = hotel_feature_columns() if is_hotel else poi_feature_columns()
        rows = [build_inference_row(traveller, item, is_hotel=is_hotel) for item in items]
        df = pd.DataFrame(rows)[cols]
        cat_idx = [df.columns.get_loc(c) for c in CATEGORICAL_COLS]
        from catboost import Pool
        pool = Pool(df, cat_features=cat_idx)
        preds = model.predict(pool)
        return [float(max(0.0, min(100.0, p))) for p in preds]

    # Rule-based fallback
    profile = _traveller_to_profile(traveller)
    return [utility_score(profile, item, is_hotel=is_hotel) for item in items]


def score_pois(traveller: dict, pois: List[dict]) -> List[float]:
    return score_items(traveller, pois, is_hotel=False)


def score_hotels(traveller: dict, hotels: List[dict]) -> List[float]:
    return score_items(traveller, hotels, is_hotel=True)


def model_status() -> Dict[str, str]:
    """Reports which scoring path is active, so the API/UI can be transparent about it."""
    return {
        "poi_model": "catboost" if _get_poi_model() is not None else "rule_based_fallback",
        "hotel_model": "catboost" if _get_hotel_model() is not None else "rule_based_fallback",
    }