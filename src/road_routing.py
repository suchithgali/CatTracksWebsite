from __future__ import annotations

import logging
import os
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)
DEFAULT_ROUTING_URL = "https://router.project-osrm.org"
DEFAULT_GEOCODING_URL = "https://nominatim.openstreetmap.org/search"
MERCED_VIEWBOX = "-120.60,37.45,-120.30,37.25"
MERCED_BOUNDS = (37.25, 37.45, -120.60, -120.30)


def _step_instruction(step: dict[str, Any]) -> str:
    maneuver = step.get("maneuver", {})
    modifier = str(maneuver.get("modifier", "")).replace("-", " ")
    maneuver_type = str(maneuver.get("type") or "continue").replace("-", " ")
    road_name = step.get("name") or "the road"
    if maneuver_type == "depart":
        return f"Start on {road_name}"
    if maneuver_type == "arrive":
        return "Arrive at your destination"
    if maneuver_type == "roundabout":
        exit_number = maneuver.get("exit")
        suffix = f", take exit {exit_number}" if exit_number else ""
        return f"Enter the roundabout{suffix} onto {road_name}"
    action = {
        "turn": f"Turn {modifier}".strip(),
        "new name": "Continue",
        "merge": f"Merge {modifier}".strip(),
        "on ramp": "Take the ramp",
        "off ramp": "Take the exit",
        "fork": f"Keep {modifier}".strip(),
        "continue": "Continue",
    }.get(maneuver_type, "Continue")
    return f"{action} onto {road_name}" if road_name != "the road" else action


def geocode_location(location: str) -> dict[str, float | str]:
    """Resolve a user-entered address or place to coordinates."""
    try:
        response = requests.get(
            os.environ.get("CATTRACKS_GEOCODING_URL", DEFAULT_GEOCODING_URL),
            params={
                "q": location,
                "format": "jsonv2",
                "limit": 1,
                "viewbox": MERCED_VIEWBOX,
                "bounded": 1,
            },
            headers={"User-Agent": "CatTracks/1.0 (UC Merced route planner)"},
            timeout=5,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            raise ValueError("Location was not found")
        result = results[0]
        latitude = float(result["lat"])
        longitude = float(result["lon"])
        min_lat, max_lat, min_lon, max_lon = MERCED_BOUNDS
        if not (min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon):
            raise ValueError("Location is outside the Merced CatTracks service area")
        return {
            "name": location,
            "latitude": latitude,
            "longitude": longitude,
        }
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError) as error:
        if str(error) == "Location is outside the Merced CatTracks service area":
            raise ValueError(str(error)) from error
        raise ValueError(f"Could not find location: {location}") from error


def route_between(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Return road geometry, distance, and duration for one access leg."""
    return _route_pair(first, second)


def _route_pair(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Return road geometry, distance, and directions for one pair."""
    fallback = {
        "type": "LineString",
        "coordinates": [
            [float(first["longitude"]), float(first["latitude"])],
            [float(second["longitude"]), float(second["latitude"])],
        ],
    }

    coordinates = ";".join(
        f'{float(point["longitude"])},{float(point["latitude"])}'
        for point in (first, second)
    )
    base_url = os.environ.get("CATTRACKS_ROUTING_URL", DEFAULT_ROUTING_URL).rstrip("/")
    url = f"{base_url}/route/v1/driving/{coordinates}"

    try:
        response = requests.get(
            url,
            params={"overview": "full", "geometries": "geojson", "steps": "true"},
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
            "directions": [
                {
                    "instruction": _step_instruction(step),
                    "distance_meters": float(step.get("distance", 0)),
                    "duration_seconds": float(step.get("duration", 0)),
                }
                for leg in route.get("legs", [])
                for step in leg.get("steps", [])
                if step.get("distance", 0) > 0
            ],
        }
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        LOGGER.warning("Road routing unavailable; using direct stop geometry", exc_info=True)
        return {"geometry": fallback, "source": "stops", "directions": []}


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
        return {"geometry": fallback, "source": "stops", "directions": []}

    geometries: list[list[float]] = []
    directions: list[dict[str, float | str]] = []
    total_distance = 0.0
    total_duration = 0.0
    source = "osrm"

    for first, second in zip(points, points[1:]):
        leg = route_between(first, second)
        coordinates = leg["geometry"]["coordinates"]
        if not geometries:
            geometries.extend(coordinates)
        else:
            geometries.extend(coordinates[1:])
        directions.extend(leg.get("directions", []))
        total_distance += float(leg.get("distance_meters", 0))
        total_duration += float(leg.get("duration_seconds", 0))
        if leg.get("source") != "osrm":
            source = "stops"

    return {
        "geometry": {"type": "LineString", "coordinates": geometries},
        "source": source,
        "distance_meters": total_distance,
        "duration_seconds": total_duration,
        "directions": directions,
    }
