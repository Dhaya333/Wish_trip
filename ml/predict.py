"""
Inference-time scoring for POIs and hotels.

Tries to load a trained scikit-learn model bundle (produced by
ml/train_poi_model.py / ml/train_hotel_model.py, saved as a joblib file
containing the fitted HistGradientBoostingRegressor plus its
OrdinalEncoder and column ordering). If no trained model artifact is
present, falls back to the transparent rule-based utility function from
ml/synthetic_data.py -- this keeps the planner usable even before any
training run has happened.

NOTE: earlier versions of this file used CatBoost (models/*.cbm). We
switched to scikit-learn's HistGradientBoostingRegressor (models/*.joblib)
because CatBoost's compiled _catboost DLL is blocked outright by some
locked-down Windows security policies (Smart App Control), with no way to
grant a per-app exception. HistGradientBoostingRegressor gives the same
"gradient-boosted trees with categorical support" capability using
scikit-learn's pure-Python-distributed binaries instead.

The planner (planner/candidate_retrieval.py + planner/optimizer.py) only
calls the functions in this module -- it never needs to know whether a
trained model or the rule-based fallback produced the score.
"""
import os
from typing import Dict, List

import joblib
import pandas as pd

from ml.synthetic_data import SyntheticProfile, utility_score

POI_MODEL_PATH = "models/poi_model.joblib"
HOTEL_MODEL_PATH = "models/hotel_model.joblib"

_poi_bundle = None
_hotel_bundle = None


def _try_load_bundle(path: str):
    if not os.path.exists(path):
        return None
    try:
        return joblib.load(path)
    except Exception:
        return None


def _get_poi_bundle():
    global _poi_bundle
    if _poi_bundle is None:
        _poi_bundle = _try_load_bundle(POI_MODEL_PATH)
    return _poi_bundle


def _get_hotel_bundle():
    global _hotel_bundle
    if _hotel_bundle is None:
        _hotel_bundle = _try_load_bundle(HOTEL_MODEL_PATH)
    return _hotel_bundle


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


def _score_with_bundle(bundle: dict, rows: List[Dict]) -> List[float]:
    df = pd.DataFrame(rows)

    cat_cols = bundle["categorical_cols"]
    num_cols = bundle["numeric_cols"]
    feature_order = bundle["feature_order"]
    encoder = bundle["encoder"]
    model = bundle["model"]

    # any feature column the model was trained on but that's missing here
    # (e.g. a raw interaction-only column not available at inference time)
    # gets filled with a neutral 0 rather than crashing
    for col in cat_cols + num_cols:
        if col not in df.columns:
            df[col] = "unknown" if col in cat_cols else 0

    if cat_cols:
        df[cat_cols] = encoder.transform(df[cat_cols].astype(str))

    X = df[feature_order]
    preds = model.predict(X)
    return [float(max(0.0, min(100.0, p))) for p in preds]


def score_items(traveller: dict, items: List[dict], is_hotel: bool = False) -> List[float]:
    """
    Returns a suitability score (0-100) per item, in the same order as
    `items`. Uses the trained model when available, otherwise the
    rule-based utility function as a fallback.

    `rows` passed to the model must already be in the same shape the
    training table used (see ml/build_training_data.py) -- callers in
    planner/candidate_retrieval.py are responsible for assembling that
    shape per traveller+item pair.
    """
    bundle = _get_hotel_bundle() if is_hotel else _get_poi_bundle()

    if bundle is not None:
        rows = [_build_inference_row(traveller, item, is_hotel) for item in items]
        return _score_with_bundle(bundle, rows)

    # Rule-based fallback
    profile = _traveller_to_profile(traveller)
    return [utility_score(profile, item, is_hotel=is_hotel) for item in items]


def _build_inference_row(traveller: dict, item: dict, is_hotel: bool) -> Dict:
    """Builds one feature row matching the training table columns as closely
    as the live planner context allows. Missing engineered columns (e.g.
    travel_time_minutes, which depends on the day's route) are filled by
    the caller when known, else default via _score_with_bundle's fallback."""
    row = {
        "traveller_type": traveller["traveller_type"],
        "pace": traveller["pace"],
        "budget_level": traveller["budget_level"],
        "hotel_comfort": traveller.get("hotel_comfort", ""),
        "mobility_need": traveller["mobility_need"],
        "dietary_preference": traveller.get("dietary_preference", ""),
        "preferred_transport": traveller.get("preferred_transport", ""),
        "month": traveller.get("month", ""),
        "adults": traveller["adults"],
        "children": traveller["children"],
        "seniors": traveller["seniors"],
        "total_party_size": traveller["adults"] + traveller["children"] + traveller["seniors"],
    }
    for pref, weight in traveller.get("preferences", {}).items():
        row[f"{pref}_preference"] = weight

    if is_hotel:
        row.update({
            "hotel_id": item.get("hotel_id"),
            "comfort_level": item.get("comfort_level"),
            "star_category": item.get("star_category"),
            "quality_score": item.get("quality_score"),
            "price_per_night": item.get("price_per_night"),
            "room_capacity": item.get("room_capacity"),
            "accessibility_score": item.get("accessibility_score"),
        })
    else:
        row.update({
            "poi_id": item.get("poi_id"),
            "category": item.get("category"),
            "time_period": item.get("time_period", ""),
            # NOTE: "hotel_zone" in the training data is the zone of the
            # traveller's HOTEL (context), not the POI's own zone -- we
            # don't know that yet at this scoring step (hotel selection
            # happens once, POIs are scored independent of it), so we
            # deliberately leave it unset and let it fall back to
            # "unknown" rather than silently feeding in the wrong zone.
            "typical_duration_minutes": item.get("typical_duration_minutes"),
            "accessibility_score": item.get("accessibility_score"),
            "quality_score": item.get("quality_score"),
        })
    return row


def score_pois(traveller: dict, pois: List[dict]) -> List[float]:
    return score_items(traveller, pois, is_hotel=False)


def score_hotels(traveller: dict, hotels: List[dict]) -> List[float]:
    return score_items(traveller, hotels, is_hotel=True)


def model_status() -> Dict[str, str]:
    """Reports which scoring path is active, so the API/UI can be transparent about it."""
    return {
        "poi_model": "trained" if _get_poi_bundle() is not None else "rule_based_fallback",
        "hotel_model": "trained" if _get_hotel_bundle() is not None else "rule_based_fallback",
    }