"""
Creates all tables and loads the curated + indicative Goa seed data
(data/seed_data.py) into the configured database.

Run with:  python -m database.init_db
"""
from database.models import (
    Base, Destination, Zone, POI, Hotel, Restaurant, TransportRoute,
    LocalTravelTime,
)
from database.session import engine, SessionLocal
from data.seed_data import (
    DESTINATION, ZONES, POIS, HOTELS, RESTAURANTS, TRANSPORT_ROUTES,
    LOCAL_TRAVEL_TIMES,
)


def reset_and_seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = SessionLocal()
    try:
        destination = Destination(**DESTINATION)
        session.add(destination)
        session.flush()

        zone_objects = []
        for z in ZONES:
            zone = Zone(destination_id=destination.id, **z)
            session.add(zone)
            zone_objects.append(zone)
        session.flush()

        for p in POIS:
            data = dict(p)
            zone_index = data.pop("zone")
            session.add(POI(zone_id=zone_objects[zone_index].id, **data))

        for h in HOTELS:
            data = dict(h)
            zone_index = data.pop("zone")
            session.add(Hotel(zone_id=zone_objects[zone_index].id, **data))

        for r in RESTAURANTS:
            data = dict(r)
            zone_index = data.pop("zone")
            session.add(Restaurant(zone_id=zone_objects[zone_index].id, **data))

        for t in TRANSPORT_ROUTES:
            session.add(TransportRoute(**t))

        for lt in LOCAL_TRAVEL_TIMES:
            o, d = lt["o"], lt["d"]
            common = dict(mode=lt["mode"], distance_km=lt["distance_km"],
                          duration_minutes=lt["duration_minutes"],
                          estimated_cost=lt["estimated_cost"])
            # store both directions since travel time is used symmetrically
            session.add(LocalTravelTime(origin_zone_id=zone_objects[o].id,
                                         destination_zone_id=zone_objects[d].id,
                                         **common))
            session.add(LocalTravelTime(origin_zone_id=zone_objects[d].id,
                                         destination_zone_id=zone_objects[o].id,
                                         **common))
            # zero-cost/time self-loop so "already at this zone" lookups are simple
        for zone in zone_objects:
            session.add(LocalTravelTime(origin_zone_id=zone.id, destination_zone_id=zone.id,
                                         mode="walk", distance_km=0, duration_minutes=0,
                                         estimated_cost=0))

        session.commit()
        print(f"Seeded {len(POIS)} POIs, {len(HOTELS)} hotels, "
              f"{len(RESTAURANTS)} restaurants across {len(ZONES)} zones.")
    finally:
        session.close()


if __name__ == "__main__":
    reset_and_seed()