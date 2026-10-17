from __future__ import annotations

import logging
import os
from typing import Any

import requests

LOGGER = logging.getLogger(__name__)
DEFAULT_ROUTING_URL = "https://router.project-osrm.org"


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

    coordinates = ";".join(
        f'{float(point["longitude"])},{float(point["latitude"])}'
        for point in points
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
        geometry = routes[0].get("geometry") if routes else None
        if not geometry or geometry.get("type") != "LineString":
            raise ValueError("Routing service returned no line geometry")
        return {"geometry": geometry, "source": "osrm"}
    except (requests.RequestException, ValueError, TypeError, KeyError, IndexError):
        LOGGER.warning("Road routing unavailable; using direct stop geometry", exc_info=True)
        return {"geometry": fallback, "source": "stops"}
