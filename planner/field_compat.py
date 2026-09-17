"""
Small field-access helpers so planner/optimizer.py doesn't repeat raw
dict-key lookups for POI attributes whose names differ across contexts
(real dataset column names, per Section: real-data schema alignment).

Centralising these means a future column rename only needs to change one
place instead of every call site in optimizer.py.
"""
from typing import Dict

from ml.schema_constants import poi_party_column


def get_duration(poi: Dict, default: int = 90) -> int:
    return poi.get("typical_duration_minutes", default)


def get_cost(poi: Dict, default: float = 0.0) -> float:
    return poi.get("base_cost", default)


def get_period_score(poi: Dict, period: str, default: int = 50) -> int:
    return poi.get(f"{period}_score", default)


def get_accessibility_score(poi: Dict, default: int = 50) -> int:
    return poi.get("accessibility_score", default)


def get_party_suitability(poi: Dict, traveller_type: str, default: int = 50) -> int:
    return poi.get(poi_party_column(traveller_type), default)