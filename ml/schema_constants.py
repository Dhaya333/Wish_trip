"""
Single source of truth for naming differences between the traveller-facing
API (planner/schemas.py) and the real dataset's column names
(data/raw/*.csv, ml/raw/*.csv).

Two things this resolves:
1. The real POI/traveller data calls the beach interest "beach" (e.g.
   `beach_affinity`, `beach_preference`), while our earlier, invented
   naming used "beaches". We keep "beach" everywhere internally now.
2. Party-suitability columns use a different suffix on POIs vs hotels:
   POIs use "*_suitability" (e.g. `solo_suitability`), hotels use
   "*_score" (e.g. `solo_score`). Both also spell "seniors" as singular
   "senior" in the column name, unlike the "seniors" traveller_type value
   used throughout the API.
"""

INTERESTS = [
    "food", "culture", "nature", "beach", "wellness", "adventure",
    "nightlife", "shopping", "history", "photography", "wildlife",
    "spirituality",
]

# traveller_type (as used in TripRequest/PreferenceWeights) -> POI column suffix
POI_PARTY_SUFFIX = {
    "solo": "solo_suitability",
    "couple": "couple_suitability",
    "family": "family_suitability",
    "friends": "friends_suitability",
    "seniors": "senior_suitability",
}

# traveller_type -> Hotel column suffix
HOTEL_PARTY_SUFFIX = {
    "solo": "solo_score",
    "couple": "couple_score",
    "family": "family_score",
    "friends": "friends_score",
    "seniors": "senior_score",
}


def poi_party_column(traveller_type: str) -> str:
    return POI_PARTY_SUFFIX.get(traveller_type, "family_suitability")


def hotel_party_column(traveller_type: str) -> str:
    return HOTEL_PARTY_SUFFIX.get(traveller_type, "family_score")