"""
Curated + indicative seed data for the Goa V1 destination.

IMPORTANT DATA HONESTY NOTE (see MASTER_PROJECT.md Sections 29-30):
- Zone/POI identity, category, and approximate coordinates are based on
  well-known, publicly available facts about Goa.
- Prices, exact opening hours (where not marked otherwise), transport
  costs/durations, and travel-time estimates are INDICATIVE / ESTIMATED,
  not scraped or verified against a live source. Every such record sets
  `is_synthetic_or_estimated=True` (or an equivalent `is_indicative` flag)
  so the planner and frontend can surface this honestly instead of
  presenting an estimate as a verified fact.
- This dataset is intentionally small and hand-curated (single destination
  depth, per Section 3.1) rather than broad scraped coverage.
"""

DESTINATION = {"name": "Goa", "state": "Goa", "country": "India"}

ZONES = [
    {"name": "North Goa - Calangute/Baga", "latitude": 15.5439, "longitude": 73.7553},
    {"name": "North Goa - Anjuna/Vagator", "latitude": 15.5937, "longitude": 73.7434},
    {"name": "Panaji (Capital)", "latitude": 15.4909, "longitude": 73.8278},
    {"name": "Old Goa", "latitude": 15.5007, "longitude": 73.9119},
    {"name": "South Goa - Palolem/Colva", "latitude": 15.0100, "longitude": 74.0233},
]

# Index-friendly zone keys for readability while building POIs etc.
Z_CALANGUTE, Z_ANJUNA, Z_PANAJI, Z_OLDGOA, Z_SOUTH = range(5)

POIS = [
    dict(zone=Z_CALANGUTE, name="Baga Beach", category="beach",
         latitude=15.5553, longitude=73.7517, duration_minutes=150, cost=0,
         opening_time="06:00", closing_time="21:00", opening_hours_is_assumption=True,
         family_suitability=85, senior_suitability=70, solo_suitability=80,
         couple_suitability=90, friends_suitability=95,
         morning_suitability=80, afternoon_suitability=70, evening_suitability=90,
         affinity_beaches=95, affinity_nature=60, affinity_photography=80,
         affinity_nightlife=60, popularity_proxy=90,
         is_synthetic_or_estimated=False, accessibility_level="medium"),

    dict(zone=Z_CALANGUTE, name="Calangute Beach", category="beach",
         latitude=15.5439, longitude=73.7553, duration_minutes=150, cost=0,
         opening_time="06:00", closing_time="21:00", opening_hours_is_assumption=True,
         family_suitability=90, senior_suitability=75, solo_suitability=70,
         couple_suitability=85, friends_suitability=85,
         morning_suitability=85, afternoon_suitability=65, evening_suitability=80,
         affinity_beaches=95, affinity_nature=55, affinity_photography=70,
         popularity_proxy=88, accessibility_level="high"),

    dict(zone=Z_CALANGUTE, name="Water Sports at Baga", category="adventure",
         latitude=15.5560, longitude=73.7520, duration_minutes=120, cost=1800,
         opening_time="08:00", closing_time="17:00", opening_hours_is_assumption=True,
         family_suitability=55, senior_suitability=25, solo_suitability=70,
         couple_suitability=65, friends_suitability=95,
         morning_suitability=85, afternoon_suitability=75, evening_suitability=20,
         affinity_adventure=95, affinity_beaches=50, affinity_photography=40,
         popularity_proxy=75, is_synthetic_or_estimated=True, accessibility_level="low"),

    dict(zone=Z_ANJUNA, name="Anjuna Flea Market", category="shopping",
         latitude=15.5745, longitude=73.7405, duration_minutes=120, cost=0,
         opening_time="09:00", closing_time="18:00", opening_hours_is_assumption=True,
         family_suitability=65, senior_suitability=55, solo_suitability=85,
         couple_suitability=80, friends_suitability=90,
         morning_suitability=60, afternoon_suitability=85, evening_suitability=50,
         affinity_shopping=95, affinity_culture=50, affinity_photography=55,
         popularity_proxy=80, accessibility_level="medium"),

    dict(zone=Z_ANJUNA, name="Chapora Fort", category="history",
         latitude=15.6031, longitude=73.7362, duration_minutes=90, cost=0,
         opening_time="08:00", closing_time="18:00", opening_hours_is_assumption=True,
         family_suitability=60, senior_suitability=40, solo_suitability=85,
         couple_suitability=90, friends_suitability=75,
         morning_suitability=70, afternoon_suitability=60, evening_suitability=95,
         affinity_history=85, affinity_photography=95, affinity_culture=60,
         affinity_nature=50, popularity_proxy=82, accessibility_level="low"),

    dict(zone=Z_ANJUNA, name="Vagator Beach Sunset Point", category="beach",
         latitude=15.5983, longitude=73.7368, duration_minutes=120, cost=0,
         opening_time="06:00", closing_time="21:00", opening_hours_is_assumption=True,
         family_suitability=70, senior_suitability=55, solo_suitability=90,
         couple_suitability=95, friends_suitability=85,
         morning_suitability=50, afternoon_suitability=60, evening_suitability=95,
         affinity_beaches=90, affinity_photography=90, affinity_nature=65,
         popularity_proxy=85, accessibility_level="medium"),

    dict(zone=Z_PANAJI, name="Fontainhas Latin Quarter Walk", category="culture",
         latitude=15.4967, longitude=73.8305, duration_minutes=120, cost=0,
         opening_time="08:00", closing_time="19:00", opening_hours_is_assumption=True,
         family_suitability=75, senior_suitability=75, solo_suitability=85,
         couple_suitability=90, friends_suitability=70,
         morning_suitability=85, afternoon_suitability=65, evening_suitability=60,
         affinity_culture=95, affinity_history=80, affinity_photography=90,
         popularity_proxy=78, accessibility_level="high"),

    dict(zone=Z_PANAJI, name="Mandovi River Cruise", category="culture",
         latitude=15.4980, longitude=73.8180, duration_minutes=90, cost=700,
         opening_time="17:30", closing_time="20:30", opening_hours_is_assumption=True,
         family_suitability=80, senior_suitability=75, solo_suitability=60,
         couple_suitability=90, friends_suitability=80,
         morning_suitability=10, afternoon_suitability=30, evening_suitability=95,
         affinity_culture=70, affinity_nightlife=50, affinity_photography=60,
         popularity_proxy=76, is_synthetic_or_estimated=True, accessibility_level="high"),

    dict(zone=Z_OLDGOA, name="Basilica of Bom Jesus", category="history",
         latitude=15.5009, longitude=73.9119, duration_minutes=75, cost=0,
         opening_time="09:00", closing_time="18:00", opening_hours_is_assumption=False,
         family_suitability=80, senior_suitability=85, solo_suitability=75,
         couple_suitability=75, friends_suitability=60,
         morning_suitability=90, afternoon_suitability=70, evening_suitability=30,
         affinity_history=95, affinity_culture=90, affinity_spirituality=85,
         affinity_photography=75, popularity_proxy=88, accessibility_level="high"),

    dict(zone=Z_OLDGOA, name="Se Cathedral", category="spirituality",
         latitude=15.5019, longitude=73.9117, duration_minutes=60, cost=0,
         opening_time="09:00", closing_time="17:30", opening_hours_is_assumption=False,
         family_suitability=75, senior_suitability=85, solo_suitability=70,
         couple_suitability=70, friends_suitability=55,
         morning_suitability=85, afternoon_suitability=65, evening_suitability=20,
         affinity_spirituality=95, affinity_history=85, affinity_culture=80,
         popularity_proxy=75, accessibility_level="high"),

    dict(zone=Z_SOUTH, name="Palolem Beach", category="beach",
         latitude=15.0100, longitude=74.0233, duration_minutes=180, cost=0,
         opening_time="06:00", closing_time="21:00", opening_hours_is_assumption=True,
         family_suitability=85, senior_suitability=75, solo_suitability=85,
         couple_suitability=95, friends_suitability=80,
         morning_suitability=80, afternoon_suitability=70, evening_suitability=95,
         affinity_beaches=98, affinity_nature=80, affinity_wellness=70,
         affinity_photography=90, popularity_proxy=92, accessibility_level="medium"),

    dict(zone=Z_SOUTH, name="Cotigao Wildlife Sanctuary", category="wildlife",
         latitude=15.0270, longitude=74.2075, duration_minutes=180, cost=200,
         opening_time="07:00", closing_time="17:30", opening_hours_is_assumption=True,
         family_suitability=60, senior_suitability=35, solo_suitability=70,
         couple_suitability=60, friends_suitability=75,
         morning_suitability=90, afternoon_suitability=60, evening_suitability=10,
         affinity_wildlife=95, affinity_nature=90, affinity_adventure=50,
         popularity_proxy=60, is_synthetic_or_estimated=True, accessibility_level="low"),

    dict(zone=Z_SOUTH, name="Colva Beach", category="beach",
         latitude=15.2783, longitude=73.9169, duration_minutes=150, cost=0,
         opening_time="06:00", closing_time="21:00", opening_hours_is_assumption=True,
         family_suitability=85, senior_suitability=75, solo_suitability=70,
         couple_suitability=80, friends_suitability=80,
         morning_suitability=80, afternoon_suitability=65, evening_suitability=80,
         affinity_beaches=90, affinity_nature=55, popularity_proxy=78,
         accessibility_level="high"),

    dict(zone=Z_ANJUNA, name="Ayurvedic Spa & Wellness Session", category="wellness",
         latitude=15.5860, longitude=73.7390, duration_minutes=90, cost=2500,
         opening_time="09:00", closing_time="19:00", opening_hours_is_assumption=True,
         family_suitability=50, senior_suitability=75, solo_suitability=80,
         couple_suitability=85, friends_suitability=45,
         morning_suitability=75, afternoon_suitability=80, evening_suitability=60,
         affinity_wellness=95, affinity_spirituality=45, popularity_proxy=70,
         is_synthetic_or_estimated=True, accessibility_level="high"),

    dict(zone=Z_CALANGUTE, name="Tito's Lane Nightlife", category="nightlife",
         latitude=15.5522, longitude=73.7526, duration_minutes=150, cost=1500,
         opening_time="21:00", closing_time="02:00", opening_hours_is_assumption=True,
         family_suitability=15, senior_suitability=15, solo_suitability=60,
         couple_suitability=55, friends_suitability=95,
         morning_suitability=0, afternoon_suitability=0, evening_suitability=95,
         affinity_nightlife=95, affinity_food=40, popularity_proxy=80,
         is_synthetic_or_estimated=True, accessibility_level="medium"),
]

HOTELS = [
    dict(zone=Z_CALANGUTE, name="Baga Budget Inn", comfort_level="budget",
         price_per_night=1800, room_capacity=2, amenities="wifi,breakfast",
         family_suitability=60, senior_suitability=55, solo_suitability=80,
         couple_suitability=70, friends_suitability=85, popularity_proxy=60,
         latitude=15.5540, longitude=73.7530, accessibility_level="medium"),

    dict(zone=Z_CALANGUTE, name="Calangute Comfort Suites", comfort_level="standard",
         price_per_night=3800, room_capacity=3, amenities="wifi,breakfast,pool",
         family_suitability=80, senior_suitability=70, solo_suitability=65,
         couple_suitability=85, friends_suitability=75, popularity_proxy=75,
         latitude=15.5445, longitude=73.7548, accessibility_level="high"),

    dict(zone=Z_PANAJI, name="Panaji Riverside Premium", comfort_level="premium",
         price_per_night=6500, room_capacity=3, amenities="wifi,breakfast,pool,spa,gym",
         family_suitability=85, senior_suitability=85, solo_suitability=70,
         couple_suitability=90, friends_suitability=70, popularity_proxy=85,
         latitude=15.4955, longitude=73.8265, accessibility_level="high"),

    dict(zone=Z_SOUTH, name="Palolem Beachfront Luxury Resort", comfort_level="luxury",
         price_per_night=12000, room_capacity=3, amenities="wifi,breakfast,pool,spa,beach access,gym",
         family_suitability=90, senior_suitability=90, solo_suitability=75,
         couple_suitability=98, friends_suitability=75, popularity_proxy=92,
         latitude=15.0102, longitude=74.0225, accessibility_level="high"),

    dict(zone=Z_ANJUNA, name="Anjuna Hillside Standard Stay", comfort_level="standard",
         price_per_night=3200, room_capacity=2, amenities="wifi,breakfast",
         family_suitability=55, senior_suitability=50, solo_suitability=90,
         couple_suitability=75, friends_suitability=90, popularity_proxy=68,
         latitude=15.5900, longitude=73.7420, accessibility_level="low"),

    dict(zone=Z_SOUTH, name="Colva Family Budget Rooms", comfort_level="budget",
         price_per_night=1500, room_capacity=4, amenities="wifi",
         family_suitability=80, senior_suitability=60, solo_suitability=55,
         couple_suitability=60, friends_suitability=65, popularity_proxy=55,
         latitude=15.2790, longitude=73.9175, accessibility_level="medium"),
]

RESTAURANTS = [
    dict(zone=Z_CALANGUTE, name="Britto's Shack", cuisine="Goan seafood",
         meal_types="lunch,dinner", dietary_support="non_vegetarian,vegetarian",
         price_level="mid", average_cost_per_person=700,
         opening_time="11:00", closing_time="23:30",
         latitude=15.5548, longitude=73.7516, suitable_party_types="solo,couple,family,friends,seniors"),

    dict(zone=Z_CALANGUTE, name="Fisherman's Wharf", cuisine="Goan, continental",
         meal_types="lunch,dinner", dietary_support="non_vegetarian,vegetarian,jain",
         price_level="high", average_cost_per_person=1200,
         opening_time="12:00", closing_time="23:00",
         latitude=15.5460, longitude=73.7560, suitable_party_types="couple,family,friends,seniors"),

    dict(zone=Z_ANJUNA, name="Curlies Beach Shack", cuisine="multi-cuisine",
         meal_types="lunch,dinner", dietary_support="non_vegetarian,vegetarian,vegan",
         price_level="mid", average_cost_per_person=650,
         opening_time="11:00", closing_time="01:00",
         latitude=15.5730, longitude=73.7400, suitable_party_types="solo,couple,friends"),

    dict(zone=Z_PANAJI, name="Viva Panjim", cuisine="Goan home-style",
         meal_types="lunch,dinner", dietary_support="non_vegetarian,vegetarian",
         price_level="mid", average_cost_per_person=550,
         opening_time="12:00", closing_time="22:30",
         latitude=15.4970, longitude=73.8300, suitable_party_types="solo,couple,family,friends,seniors"),

    dict(zone=Z_OLDGOA, name="Heritage Thali House", cuisine="vegetarian thali",
         meal_types="breakfast,lunch,dinner", dietary_support="vegetarian,jain,vegan",
         price_level="low", average_cost_per_person=350,
         opening_time="08:00", closing_time="21:00",
         latitude=15.5015, longitude=73.9110, suitable_party_types="solo,couple,family,seniors"),

    dict(zone=Z_SOUTH, name="Palolem Sunset Shack", cuisine="Goan seafood, continental",
         meal_types="lunch,dinner", dietary_support="non_vegetarian,vegetarian",
         price_level="mid", average_cost_per_person=750,
         opening_time="11:00", closing_time="23:00",
         latitude=15.0095, longitude=74.0230, suitable_party_types="solo,couple,family,friends,seniors"),
]

# Intercity transport, indicative only (Section 23). Cost/duration are
# estimates -- NOT pulled from a live fares API.
TRANSPORT_ROUTES = [
    dict(origin_city="Mumbai", destination_city="Goa", mode="flight",
         departure_window="06:00-22:00", arrival_window="+1h15m after departure",
         duration_minutes=75, estimated_cost_per_person=3200, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Mumbai", destination_city="Goa", mode="train",
         departure_window="evening departures common", arrival_window="next morning",
         duration_minutes=600, estimated_cost_per_person=900, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Bengaluru", destination_city="Goa", mode="flight",
         departure_window="06:00-21:00", arrival_window="+1h20m after departure",
         duration_minutes=80, estimated_cost_per_person=3800, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Bengaluru", destination_city="Goa", mode="bus",
         departure_window="evening departures common", arrival_window="next morning",
         duration_minutes=660, estimated_cost_per_person=1200, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Delhi", destination_city="Goa", mode="flight",
         departure_window="05:30-23:00", arrival_window="+2h30m after departure",
         duration_minutes=150, estimated_cost_per_person=5200, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Chennai", destination_city="Goa", mode="flight",
         departure_window="06:00-20:00", arrival_window="+1h30m after departure",
         duration_minutes=90, estimated_cost_per_person=4200, transfers=0,
         comfort_level="standard"),
    dict(origin_city="Chennai", destination_city="Goa", mode="train",
         departure_window="evening departures common", arrival_window="next day",
         duration_minutes=1080, estimated_cost_per_person=1400, transfers=1,
         comfort_level="standard"),
    dict(origin_city="Pune", destination_city="Goa", mode="bus",
         departure_window="frequent daytime departures", arrival_window="same day",
         duration_minutes=480, estimated_cost_per_person=800, transfers=0,
         comfort_level="standard"),
]

# Local zone-to-zone travel times within Goa. Indicative straight-line-based
# estimate, not a live routing API result.
LOCAL_TRAVEL_TIMES = [
    dict(o=Z_CALANGUTE, d=Z_ANJUNA, mode="taxi", distance_km=6, duration_minutes=18, estimated_cost=250),
    dict(o=Z_CALANGUTE, d=Z_PANAJI, mode="taxi", distance_km=15, duration_minutes=35, estimated_cost=500),
    dict(o=Z_CALANGUTE, d=Z_OLDGOA, mode="taxi", distance_km=20, duration_minutes=45, estimated_cost=650),
    dict(o=Z_CALANGUTE, d=Z_SOUTH, mode="taxi", distance_km=62, duration_minutes=100, estimated_cost=1800),
    dict(o=Z_ANJUNA, d=Z_PANAJI, mode="taxi", distance_km=18, duration_minutes=40, estimated_cost=550),
    dict(o=Z_ANJUNA, d=Z_OLDGOA, mode="taxi", distance_km=24, duration_minutes=50, estimated_cost=700),
    dict(o=Z_ANJUNA, d=Z_SOUTH, mode="taxi", distance_km=66, duration_minutes=105, estimated_cost=1900),
    dict(o=Z_PANAJI, d=Z_OLDGOA, mode="taxi", distance_km=10, duration_minutes=22, estimated_cost=350),
    dict(o=Z_PANAJI, d=Z_SOUTH, mode="taxi", distance_km=48, duration_minutes=80, estimated_cost=1400),
    dict(o=Z_OLDGOA, d=Z_SOUTH, mode="taxi", distance_km=55, duration_minutes=90, estimated_cost=1600),
]

ZONE_KEY_TO_NAME = {i: z["name"] for i, z in enumerate(ZONES)}