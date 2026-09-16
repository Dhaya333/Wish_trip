# Wishtrip — Goa Trip Planner

A trip-planning app for Goa that turns a traveller's preferences into a
personalised, day-by-day itinerary — hotel, activities, meals, transport,
and a cost breakdown — using a trained ML suitability model plus a
constraint-aware scheduling optimiser. No LLM is used to generate the
plan; every recommendation traces back to real scoring signals and comes
with a plain-language "why this was picked" explanation.

---

## What it does

You tell it:
- Where you're travelling from and your dates
- Who's travelling (solo / couple / family / friends / seniors, party size)
- How much you care about each of 12 interests (food, beaches, culture,
  adventure, nightlife, wellness, etc.) — as independent 0–100 sliders
- Your pace (easy-going / balanced / packed), budget, hotel comfort level,
  dietary needs, mobility needs, and transport preference

It gives you back:
- A recommended hotel, with a reason it fits your trip
- A day-by-day schedule of activities (morning/afternoon/evening), each
  with a plain-language explanation of why it was chosen for you
  specifically
- Suggested meals per day matching your dietary preference
- Suggested intercity transport
- A full cost breakdown (transport, hotel, activities, meals, local
  travel, grand total, per-person estimate)
- Explicit feasibility notes if your budget/constraints can't all be
  satisfied — it never silently blows past your budget without saying so

Two example trips with different preferences produce visibly different
itineraries — this isn't a fixed template, it's actually driven by what
you tell it.

---

## How it works

```
Your preferences (Streamlit UI)
        │
        ▼
FastAPI backend  ──►  Validates the request
        │
        ▼
Candidate retrieval  ──►  Pulls matching hotels/POIs/restaurants from Postgres
        │
        ▼
ML suitability scoring  ──►  Trained model ranks every candidate for YOU
        │                     (falls back to a transparent rule-based
        │                      score if no trained model is present yet)
        ▼
Constraint-aware optimiser  ──►  Builds each day: no duplicate activities,
        │                         respects opening hours, your pace, your
        │                         budget, accessibility needs
        ▼
Explanation generator  ──►  Turns scoring signals into plain-language
        │                    "why this was picked" text (no LLM)
        ▼
Structured itinerary  ──►  Rendered back in the Streamlit UI
```

**Tech stack:** FastAPI (backend), Streamlit (frontend), PostgreSQL
(data), scikit-learn `HistGradientBoostingRegressor` (the ML model),
Docker (recommended way to run it, especially on Windows — see below).

---

## Project layout

```
wishtrip-goa-planner/
├── data/           # Reference data: zones, POIs, hotels, restaurants,
│                   # transport, travel times (loaded from data/raw/*.csv)
├── database/       # SQLAlchemy models + DB setup
├── ml/             # Training data building, model training, inference
├── planner/        # Validation, candidate retrieval, optimiser,
│                   # explanations, the pipeline that ties it all together
├── backend/        # FastAPI app (the only thing the frontend talks to)
├── frontend/       # Streamlit UI
├── tests/          # pytest suite covering hard constraints
├── models/         # Trained model files land here (generated, not source)
├── Dockerfile, docker-compose.yml   # Recommended way to run everything
└── requirements.txt
```

See `FILE_STRUCTURE.md` for the full file-by-file breakdown.

---

## How to use it

### Option A — Docker (recommended, especially on Windows)

Windows security features like Smart App Control can block compiled
Python packages (numpy/scipy/scikit-learn) outright with no way to grant
an exception short of reinstalling Windows. Running everything inside
Docker sidesteps this entirely, since it's a Linux environment.

```bash
docker compose up -d --build      # starts Postgres + the app together
docker compose exec app bash      # open a shell inside the app container
```

Then, inside that shell:

```bash
python -m database.init_db          # load Goa reference data into Postgres
python -m ml.build_training_data    # build training tables from your interaction data
python -m ml.train_poi_model        # train the POI suitability model
python -m ml.train_hotel_model      # train the hotel suitability model
python -m pytest tests/ -v          # confirm everything works (should be all green)
```

The backend is already running at `http://localhost:8000` once the
containers are up (the Dockerfile starts it automatically).

### Option B — Run natively (Mac/Linux, or Windows if Smart App Control isn't an issue)

```bash
python3 -m venv .venv
source .venv/bin/activate                # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                     # edit DATABASE_URL if using Postgres,
                                          # or leave unset to use a local SQLite fallback

python3 -m database.init_db
python3 -m ml.build_training_data
python3 -m ml.train_poi_model
python3 -m ml.train_hotel_model
python3 -m pytest tests/ -v
```

### Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```
Check it's up: `http://localhost:8000/health`
Interactive API docs: `http://localhost:8000/docs`

### Start the frontend (in a second terminal, backend still running)

```bash
export BACKEND_URL=http://localhost:8000   # Windows PowerShell: $env:BACKEND_URL="http://localhost:8000"
streamlit run frontend/app.py
```

Open the printed `http://localhost:8501` link, fill in your trip details,
and click **"Plan my trip."**

For the full step-by-step with expected output at each stage, see
`RUNBOOK.md`.

---

## Data sources and honesty

The Goa reference data (zones, POIs, hotels, restaurants, transport,
travel times) lives in `data/raw/*.csv`. The ML training data
(traveller profiles + interaction scores) lives in `ml/raw/*.csv`.
Neither is scraped from a live source — prices, durations, and travel
times are curated/indicative unless otherwise noted, and the app is
upfront about this rather than presenting estimates as verified facts.

---

## Running the tests

```bash
python -m pytest tests/ -v
```

The suite specifically checks the constraints that matter most in a trip
planner: no duplicate activities across the itinerary, no scheduling
outside opening hours, per-day and total budget ceilings are respected,
and accessibility/mobility needs are treated as hard constraints, not
suggestions.