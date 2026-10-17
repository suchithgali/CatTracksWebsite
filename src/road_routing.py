from __future__ import annotations

import logging
import os
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)
DEFAULT_ROUTING_URL = "https://router.project-osrm.org"
DEFAULT_GEOCODING_URL = "https://nominatim.openstreetmap.org/search"


def geocode_location(location: str) -> dict[str, float | str]:
    """Resolve a user-entered address or place to coordinates."""
    try:
        response = requests.get(
            os.environ.get("CATTRACKS_GEOCODING_URL", DEFAULT_GEOCODING_URL),
            params={"q": location, "format": "jsonv2", "limit": 1},
            headers={"User-Agent": "CatTracks/1.0 (UC Merced route planner)"},
            timeout=5,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError("Location was not found")
        result = results[0]
        return {
            "name": location,
            "latitude": float(result["lat"]),
            "longitude": float(result["lon"]),
        }
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as error:
        raise ValueError(f"Could not find location: {location}") from error


def route_between(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Return road geometry, distance, and duration for one access leg."""
    fallback = {
        "type": "LineString",
        "coordinates": [
            [float(first["longitude"]), float(first["latitude"])],
            [float(second["longitude"]), float(second["latitude"])],
        ],
    }

    coordinates = (
        f'{float(first["longitude"])},{float(first["latitude"])};'
        f'{float(second["longitude"])},{float(second["latitude"])}'
    )
    base_url = os.environ.get("CATTRACKS_ROUTING_URL", DEFAULT_ROUTING_URL).rstrip("/")
    url = f"{base_url}/route/v1/driving/{coordinates}"

    try:
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson", "steps": "false"},
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
        routes = payload.get("routes", [])
        route = routes[0] if routes else None
        geometry = route.get("geometry") if route else None
        if not geometry or geometry.get("type") != "LineString":
            raise ValueError("Routing service returned no line geometry")
        return {
            "geometry": geometry,
            "source": "osrm",
            "distance_meters": float(route["distance"]),
            "duration_seconds": float(route["duration"]),
        }
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        LOGGER.warning("Road routing unavailable; using direct stop geometry", exc_info=True)
        return {"geometry": fallback, "source": "stops"}


def route_geometry(points: list[dict[str, Any]]) -> dict[str, Any]:
    """Return road-following GeoJSON for the route's stop coordinates."""
    fallback = {
        "type": "LineString",
        "coordinates": [
            [float(point["longitude"]), float(point["latitude"])]
            for point in points
        ],
    }
    if len(points) < 2:
        return {"geometry": fallback, "source": "stops"}

    return route_between(points[0], points[-1])
