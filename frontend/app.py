"""
Streamlit frontend (Section 10 -- Streamlit responsibilities: collect
inputs, render interactive preference bars, show validation errors, send
structured request to FastAPI, display itinerary/costs/assumptions/why).

Contains NO planning logic itself -- everything is delegated to the
FastAPI backend's POST /plan endpoint.

Run with:
    streamlit run frontend/app.py
"""
import os
from datetime import date, timedelta

import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

INTERESTS = [
    "food", "culture", "nature", "beaches", "wellness", "adventure",
    "nightlife", "shopping", "history", "photography", "wildlife",
    "spirituality",
]

st.set_page_config(page_title="Wishtrip Goa Planner", layout="wide")
st.title("🌴 Goa Trip Planner")
st.caption("ML suitability ranking + constraint-aware optimisation -- no LLM is used to generate this plan.")

# ---------------------------------------------------------------- Step 1
st.header("1. Trip Basics")
col1, col2, col3 = st.columns(3)
with col1:
    origin_city = st.text_input("Origin city", "Mumbai")
    destination = st.text_input("Destination", "Goa", disabled=True)
with col2:
    start_date = st.date_input("Travel start date", date.today() + timedelta(days=30))
with col3:
    end_date = st.date_input("Travel end date", date.today() + timedelta(days=34))

nights = (end_date - start_date).days
if nights < 1:
    st.error("End date must be after start date.")
else:
    st.info(f"Nights: {nights}")

# ---------------------------------------------------------------- Step 2
st.header("2. Traveller")
col1, col2 = st.columns(2)
with col1:
    traveller_type = st.selectbox("Traveller type", ["solo", "couple", "family", "friends", "seniors"])
with col2:
    c1, c2, c3 = st.columns(3)
    adults = c1.number_input("Adults", min_value=1, value=2)
    children = c2.number_input("Children", min_value=0, value=0)
    seniors = c3.number_input("Seniors", min_value=0, value=0)

# ---------------------------------------------------------------- Step 3
st.header("3. Interest Preference Bars")
st.caption("These are independent preference weights, not probabilities -- they don't need to sum to 100.")
preferences = {}
cols = st.columns(3)
for i, interest in enumerate(INTERESTS):
    with cols[i % 3]:
        preferences[interest] = st.slider(interest.capitalize(), 0, 100, 50)

# ---------------------------------------------------------------- Pace / Budget / Comfort
st.header("4. Pace, Budget & Comfort")
col1, col2, col3 = st.columns(3)
with col1:
    pace = st.selectbox("Pace", ["easy_going", "balanced", "packed"],
                         format_func=lambda p: p.replace("_", "-").title())
with col2:
    use_budget = st.checkbox("Set a hard total budget?", value=True)
    budget_total = st.number_input("Total trip budget (INR, whole party)", min_value=1000,
                                    value=60000, step=1000) if use_budget else None
with col3:
    hotel_comfort = st.selectbox("Hotel comfort", ["budget", "standard", "premium", "luxury"])

# ---------------------------------------------------------------- Optional inputs
st.header("5. Optional Inputs")
col1, col2, col3 = st.columns(3)
with col1:
    dietary_preference = st.selectbox(
        "Dietary preference",
        ["no_preference", "vegetarian", "vegan", "jain", "non_vegetarian"])
with col2:
    mobility_need = st.selectbox("Mobility needs", ["none", "reduced_walking", "wheelchair"])
with col3:
    preferred_transport = st.selectbox(
        "Preferred transport",
        ["balanced", "lowest_cost", "fastest", "public_transport", "taxi_private"])

st.divider()

if st.button("Plan my trip", type="primary", disabled=nights < 1):
    payload = {
        "origin_city": origin_city,
        "destination": destination,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "nights": nights,
        "traveller_type": traveller_type,
        "adults": adults,
        "children": children,
        "seniors": seniors,
        "preference_weights": preferences,
        "pace": pace,
        "budget_total": budget_total,
        "hotel_comfort": hotel_comfort,
        "dietary_preference": dietary_preference,
        "mobility_need": mobility_need,
        "preferred_transport": preferred_transport,
    }

    with st.spinner("Planning your trip..."):
        try:
            resp = requests.post(f"{BACKEND_URL}/plan", json=payload, timeout=60)
            resp.raise_for_status()
            plan = resp.json()
        except requests.RequestException as exc:
            st.error(f"Could not reach the planning backend: {exc}")
            st.stop()

    # -------------------------------------------------------- Trip summary
    st.header("Trip Summary")
    st.write(plan["planning_summary"])
    if not plan["feasible"]:
        st.warning("This plan does not fully fit your constraints -- see notes below.")
    for note in plan.get("feasibility_notes", []):
        st.warning(note)

    # -------------------------------------------------------- Transport
    if plan.get("transport"):
        st.header("Transport")
        t = plan["transport"]
        st.write(f"**{t['mode'].title()}** — ~{t['duration_minutes']} min, "
                 f"INR {t['estimated_cost_per_person']:,.0f}/person "
                 f"(total INR {t['total_cost']:,.0f}, round trip, indicative)")

    # -------------------------------------------------------- Hotel
    if plan.get("hotel"):
        st.header("Hotel")
        h = plan["hotel"]
        st.write(f"**{h['name']}** ({h['comfort_level'].title()}) — {h['zone']}")
        st.write(f"INR {h['price_per_night']:,.0f}/night — total INR {h['total_stay_cost']:,.0f}")
        st.caption(h["why_selected"])

    # -------------------------------------------------------- Days
    for day in plan.get("days", []):
        st.header(f"Day {day['day_number']} — {day['date']} ({day['zone_focus']})")
        st.write(day["day_summary"])
        for act in day["activities"]:
            with st.expander(f"{act['period'].title()}: {act['name']} ({act['duration_minutes']} min)"):
                st.write(f"Category: {act['category']} — Zone: {act['zone']} — Cost: INR {act['cost']:,.0f}")
                st.write(act["why_selected"])
                for a in act.get("assumptions", []):
                    st.caption(f"⚠️ {a}")
        if day["meals"]:
            st.write("**Meals:**")
            for meal in day["meals"]:
                st.write(f"- {meal['meal_type'].title()}: {meal['name']} "
                         f"(~INR {meal['estimated_cost_per_person']:,.0f}/person, {meal['zone']})")
        st.caption(f"Estimated day cost: INR {day['estimated_day_cost']:,.0f} — "
                   f"local travel ~{day['travel_time_minutes']} min")

    # -------------------------------------------------------- Cost breakdown
    if plan.get("cost_breakdown"):
        st.header("Cost Breakdown")
        cb = plan["cost_breakdown"]
        st.table({
            "Category": ["Transport", "Hotel", "Activities", "Meals", "Local transport", "Total", "Per person"],
            "Amount (INR)": [cb["transport_total"], cb["hotel_total"], cb["activities_total"],
                              cb["meals_total"], cb["local_transport_total"], cb["grand_total"],
                              cb["per_person_estimate"]],
        })

    # -------------------------------------------------------- Assumptions
    if plan.get("assumptions"):
        st.header("Assumptions")
        for a in plan["assumptions"]:
            st.caption(f"⚠️ {a}")