from pathlib import Path
import os

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_GTFS_DIR = PROJECT_ROOT / "data" / "gtfs_official"
GTFS_DIR = Path(os.environ.get("CATTRACKS_GTFS_DIR", PROJECT_ROOT / "data" / "gtfs"))


def load_stops() -> pd.DataFrame:
    """Load stop IDs, names, and coordinates."""
    stops = pd.read_csv(GTFS_DIR / "stops.txt", dtype={"stop_id": str})
    stops["stop_lat"] = pd.to_numeric(stops["stop_lat"])
    stops["stop_lon"] = pd.to_numeric(stops["stop_lon"])
    return stops


def load_routes() -> pd.DataFrame:
    """Load route definitions."""
    return pd.read_csv(
        GTFS_DIR / "routes.txt",
        dtype={
            "route_id": str,
            "agency_id": str,
            "route_short_name": str,
            "route_long_name": str,
        },
    )


def load_trips() -> pd.DataFrame:
    """Load trip metadata."""
    return pd.read_csv(
        GTFS_DIR / "trips.txt",
        dtype={
            "trip_id": str,
            "route_id": str,
            "service_id": str,
            "trip_headsign": str,
        },
    )


def load_stop_times() -> pd.DataFrame:
    """Load ordered stop events for each trip."""
    stop_times = pd.read_csv(
        GTFS_DIR / "stop_times.txt",
        dtype={
            "trip_id": str,
            "stop_id": str,
            "arrival_time": str,
            "departure_time": str,
            "stop_headsign": str,
            "pickup_type": str,
            "drop_off_type": str,
        },
    )
    stop_times["stop_sequence"] = pd.to_numeric(
        stop_times["stop_sequence"],
        errors="raise",
    )
    return stop_times


def load_gtfs() -> dict[str, pd.DataFrame]:
    """Load the complete GTFS feed."""
    return {
        "stops": load_stops(),
        "routes": load_routes(),
        "trips": load_trips(),
        "stop_times": load_stop_times(),
    }