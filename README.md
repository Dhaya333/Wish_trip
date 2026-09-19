# Wishtrip — Goa Trip Planner

A trip-planning app for Goa that turns a traveller's preferences into a
personalised, day-by-day itinerary — hotel, activities, meals, transport,
and a cost breakdown — using a trained ML suitability model plus a
constraint-aware scheduling optimiser. No LLM is used to generate the
plan; every recommendation traces back to real scoring signals and comes
with a plain-language "why this was picked" explanation.

**Live demo:** `https://wish-trip-frontend.onrender.com` *(replace with
your actual deployed frontend URL)*

---

## What it does

You tell it:
- Where you're travelling from and your dates
- Who's travelling (solo / couple / family / friends / seniors, party size)
- How much you care about each of 12 interests (food, beach, culture,
  adventure, nightlife, wellness, etc.) — as independent 0–100 sliders
- Your pace (easy-going / balanced / packed), budget, hotel comfort level,
  dietary needs, mobility needs, and transport preference

It gives you back:
- A recommended hotel, with a reason it fits your trip
- A day-by-day schedule of activities (morning/afternoon/evening), each
  with a plain-language explanation of why it was chosen for you
  specifically
- Suggested **breakfast, lunch, and dinner** per day, matching your
  dietary preference
- Suggested intercity transport
- A full cost breakdown (transport, hotel, activities, meals, local
  travel, grand total, per-person estimate)
- Explicit feasibility notes if your budget/constraints can't all be
  satisfied — it never silently blows past your budget without saying so

Two trips with different preferences produce visibly different
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
(data), scikit-learn `HistGradientBoostingRegressor` (the ML model —
switched from CatBoost, since CatBoost's compiled DLL gets blocked by
Windows Smart App Control in full enforcement mode with no workaround
short of reinstalling Windows), Docker (recommended way to run it
locally), Render (deployment).

---

## Data: real, not synthetic-only

This project trains on **real interaction data**, not invented labels:

- `data/raw/*.csv` — reference data: `zones.csv`, `pois.csv`, `hotels.csv`,
  `restaurants.csv`, `local_travel_times.csv`, `transport_routes.csv`,
  `seasonal_context.csv`. Loaded into Postgres via
  `data/load_seed_from_csv.py`.
- `ml/raw/*.csv` — training data: `travellers.csv`, `poi_interactions.csv`,
  `hotel_interactions.csv`. Each interaction row already carries a
  `synthetic_suitability_score` label and a `train`/`test` `split` column,
  which the training scripts use as-is (no re-shuffling, so results stay
  comparable run to run).

`ml/build_training_data.py` joins travellers + interactions + item
attributes into the actual tables the models train on
(`ml/raw/poi_training_table.csv`, `ml/raw/hotel_training_table.csv`).

Pricing, durations, and travel times in the reference data are
curated/indicative unless otherwise noted — the app is upfront about this
rather than presenting estimates as verified facts.

---

## Project layout

```
wishtrip-goa-planner/
├── data/           # Reference data (data/raw/*.csv) + the CSV loader
├── database/       # SQLAlchemy models matching the real schema, DB session, init
├── ml/             # schema_constants, training data builder, model
│                   # training (scikit-learn), inference/scoring
├── planner/        # Validation, candidate retrieval, optimiser,
│                   # explanations, the pipeline that ties it all together
├── backend/        # FastAPI app — the only thing the frontend talks to;
│                   # auto-seeds the database on startup if it's empty
├── frontend/       # Streamlit UI
├── tests/          # pytest suite covering hard constraints
├── models/         # Trained model files land here (generated, not source)
├── Dockerfile              # Backend container
├── Dockerfile.frontend     # Frontend (Streamlit) container
├── docker-compose.yml      # Postgres + backend, for local dev
└── requirements.txt
```

See `FILE_STRUCTURE.md` for the full file-by-file breakdown.

---

## How to run it

### Option A — Docker (recommended, especially on Windows)

Windows security features like Smart App Control can block compiled
Python packages outright, with no way to grant an exception short of
reinstalling Windows. Running everything inside Docker sidesteps this
entirely, since it's a Linux environment.

```bash
docker compose up -d --build      # starts Postgres + the backend together
docker compose exec app bash      # open a shell inside the backend container
```

Then, inside that shell:

```bash
python -m database.init_db          # load Goa reference data into Postgres
python -m ml.build_training_data    # build training tables from your interaction data
python -m ml.train_poi_model        # train the POI suitability model
python -m ml.train_hotel_model      # train the hotel suitability model
python -m pytest tests/ -v          # confirm everything works
```

The backend is already running at `http://localhost:8000` once the
containers are up. Note: the backend also auto-seeds itself on startup if
it ever finds an empty database, so the manual `init_db` step above is a
safety net, not strictly required after the first run.

### Option B — Run natively

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

### Start the frontend (second terminal, backend still running)

```bash
export BACKEND_URL=http://localhost:8000   # Windows PowerShell: $env:BACKEND_URL="http://localhost:8000"
streamlit run frontend/app.py
```

Open the printed `http://localhost:8501` link, fill in your trip details,
and click **"Plan my trip."**

---

## Deploying (Render)

Vercel can't run this app — Streamlit needs a persistent server process,
which serverless platforms structurally can't provide. Render supports
both long-running services and managed Postgres under one dashboard.

1. Push the repo to GitHub.
2. **New → PostgreSQL** on Render — free tier is fine for a demo (1 GB,
   30-day expiry; upgrade to Starter for anything longer-lived).
3. **New → Web Service** (backend) — Runtime: Docker, uses the root
   `Dockerfile`. Environment variable: `DATABASE_URL` = your Postgres's
   **Internal Database URL** (make sure it's `postgresql+psycopg2://...`,
   not just `postgresql://...`).
4. **New → Web Service** (frontend) — same repo, **Dockerfile Path:**
   `Dockerfile.frontend`. Environment variable: `BACKEND_URL` = your
   backend service's public URL.
5. The backend auto-seeds its database from `data/raw/*.csv` on first
   startup — no manual shell step needed. Make sure those CSVs are
   actually committed to git (`git ls-files data/raw/` to check), or the
   auto-seed has nothing to load.
6. Share the frontend service's public URL — that's the link people open.

Free-tier services spin down after 15 minutes of inactivity and take
~30–60 seconds to wake up on the next request — expected, not a bug.

---

## Running the tests

```bash
python -m pytest tests/ -v
```

The suite checks the constraints that matter most in a trip planner: no
duplicate activities across the itinerary, no scheduling outside opening
hours, per-day and total budget ceilings are respected, and
accessibility/mobility needs are treated as hard constraints, not
suggestions.

---

## Known quirks worth knowing

- **CatBoost was replaced with scikit-learn's `HistGradientBoostingRegressor`**
  after Windows Smart App Control blocked its compiled DLL — same idea
  (gradient-boosted trees with categorical support), no compiled-binary
  distribution risk.
- **The ML model falls back to a transparent rule-based score**
  (`ml/synthetic_data.py`'s `utility_score`) if no trained `.joblib` file
  is present yet — the app never crashes just because training hasn't run.
- **Dates in the itinerary display as `dd-mm-yyyy`**; the API itself still
  uses ISO `yyyy-mm-dd` internally (standard for JSON APIs) — only the
  Streamlit display layer reformats it.