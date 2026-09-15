"""
FastAPI backend (Section 10 -- FastAPI responsibilities: request
validation, calling planning services, returning structured itinerary
data, error handling, health endpoint).

The backend contains NO planning logic itself -- it only wires HTTP
requests to planner.pipeline.run_planning_pipeline().

Run with:
    uvicorn backend.main:app --reload --port 8000
"""
import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.session import get_session
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