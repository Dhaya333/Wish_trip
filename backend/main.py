"""
FastAPI backend 

The backend contains NO planning logic itself -- it only wires HTTP
requests to planner.pipeline.run_planning_pipeline().

Run with:
    uvicorn backend.main:app --reload --port 8000
"""
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.models import Zone
from database.session import SessionLocal, get_session
from ml.predict import model_status
from planner.pipeline import run_planning_pipeline
from planner.schemas import PlanResponse, TripRequest

logger = logging.getLogger("wishtrip_backend")

app = FastAPI(
    title="Wishtrip Goa Trip Planner API",
    description=(
        "Converts structured traveller preferences into a personalised, "
        "day-by-day Goa itinerary using ML suitability ranking + a "
        "constraint-aware optimiser. No LLM is used to generate the plan."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local prototype only -- restrict this before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def seed_database_if_empty():
    """
    Auto-seeds the database from data/raw/*.csv on startup, but ONLY if it
    looks empty (zero zones). This makes a fresh deploy (e.g. on Render,
    where a free-tier service may not offer shell access to run
    `python -m database.init_db` manually, and a free Postgres instance
    can also be reset/expire) self-heal without any manual step.

    It deliberately does NOT reset/reseed a database that already has
    data -- reset_and_seed() is only called once, the first time the app
    starts against an empty database.
    """
    session = SessionLocal()
    try:
        has_data = session.query(Zone).first() is not None
    except Exception:
        # table may not exist yet on a truly fresh database -- treat as empty
        has_data = False
    finally:
        session.close()

    if not has_data:
        logger.info("Database appears empty -- running initial seed from data/raw/*.csv")
        try:
            from data.load_seed_from_csv import reset_and_seed
            reset_and_seed()
            logger.info("Initial seed complete.")
        except Exception:
            logger.exception("Automatic database seeding failed on startup.")
    else:
        logger.info("Database already has data -- skipping auto-seed.")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "models": model_status(),
    }


@app.post("/plan", response_model=PlanResponse)
def plan_trip(req: TripRequest, session: Session = Depends(get_session)):
    try:
        return run_planning_pipeline(req, session)
    except Exception as exc:  # noqa: BLE001 -- surface a clean 500 instead of a raw traceback
        logger.exception("Planning pipeline failed")
        raise HTTPException(status_code=500, detail=f"Planning failed: {exc}") from exc


@app.get("/destinations")
def list_destinations(session: Session = Depends(get_session)):
    """Potential future endpoint (Section 37) -- currently returns the single V1 destination."""
    from database.models import Destination
    return [{"name": d.name, "state": d.state, "country": d.country}
            for d in session.query(Destination).all()]


@app.get("/zones")
def list_zones(destination: str = "Goa", session: Session = Depends(get_session)):
    """Potential future endpoint (Section 37)."""
    from planner.candidate_retrieval import get_zones
    return get_zones(session, destination)