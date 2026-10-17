from pathlib import Path
import csv
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_GTFS_DIR = PROJECT_ROOT / "data" / "gtfs_official"
GTFS_DIR = Path(os.environ.get("CATTRACKS_GTFS_DIR", PROJECT_ROOT / "data" / "gtfs"))


def _read_table(filename: str) -> list[dict[str, str]]:
    with (GTFS_DIR / filename).open(newline="", encoding="utf-8") as source:
        return list(csv.DictReader(source))


def load_stops() -> list[dict[str, str | float]]:
    """Load stop IDs, names, and coordinates."""
    return [
        {**stop, "stop_lat": float(stop["stop_lat"]), "stop_lon": float(stop["stop_lon"])}
        for stop in _read_table("stops.txt")
    ]


def load_routes() -> list[dict[str, str]]:
    """Load route definitions."""
    return _read_table("routes.txt")


def load_trips() -> list[dict[str, str]]:
    """Load trip metadata."""
    return _read_table("trips.txt")


def load_stop_times() -> list[dict[str, str | int]]:
    """Load ordered stop events for each trip."""
    return [
        {**row, "stop_sequence": int(row["stop_sequence"])}
        for row in _read_table("stop_times.txt")
    ]


def load_gtfs() -> dict[str, list[dict]]:
    """Load the complete GTFS feed."""
    return {
        "stops": load_stops(),
        "routes": load_routes(),
        "trips": load_trips(),
        "stop_times": load_stop_times(),
    }