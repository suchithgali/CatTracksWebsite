#!/usr/bin/env python3
"""Build a direction-aware OSMnx graph from Merced County GeoJSON layers.

The road centerline layer supplies the routable street topology. Road endpoints
that fall within a configurable tolerance are consolidated into junction nodes.
Address points are preserved as destination nodes, snapped to the closest road,
and connected to a new road connector node. Centerlines are split at these
connector locations so routes can enter and leave an address without jumping to
a distant road endpoint.

NENA-style direction values are interpreted as follows:

* B  - travel in both directions
* FT - travel from the first coordinate to the last coordinate
* TF - travel from the last coordinate to the first coordinate

Blank or null direction values are bidirectional by default. Change this with
``--unknown-oneway`` if a different policy is appropriate for another dataset.

Example
-------
Install the geospatial dependencies first::

    python -m pip install "osmnx>=2.1,<3" "pyogrio>=0.11"

Then run the builder::

    python build_merced_directional_graph.py \
      --roads "Road_Centerlines (2).geojson" \
      --addresses Merced_County_Site_Address_Points.geojson \
      --output-dir merced_graph

For a smaller city/campus build, pass a WGS84 bounding box:

    python build_merced_directional_graph.py ... \
      --bbox -120.60 37.15 -120.30 37.45

Outputs
-------
* merced_directional.graphml: OSMnx/NetworkX MultiDiGraph in EPSG:4326
* merced_directional.gpkg: node and directed-edge GIS layers
* address_node_map.csv: source address IDs mapped to graph/road node IDs
* unmatched_addresses.csv: addresses farther than the configured snap limit
* build_report.json: source, direction, topology, and connectivity statistics
"""

from __future__ import annotations

import argparse
import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import numpy as np
import osmnx as ox
import pandas as pd
import shapely
from shapely.geometry import LineString, Point
from shapely.ops import substring
from shapely.strtree import STRtree

LOGGER = logging.getLogger("merced_graph_builder")

ROAD_COLUMNS = [
    "OBJECTID",
    "rcl_nguid",
    "roadclass",
    "oneway",
    "speedlimit",
    "fullrdname",
    "feature_status",
]

ADDRESS_COLUMNS = [
    "OBJECTID",
    "site_nguid",
    "add_number",
    "fullrdname",
    "landmkname",
    "post_comm",
    "post_code",
    "feature_status",
]

# Used only when speedlimit is missing, zero, or implausibly low.
ROAD_CLASS_SPEED_MPH = {
    "INTERSTATE": 65.0,
    "RURAL HIGHWAY": 55.0,
    "HIGHWAY MAJOR": 55.0,
    "RURAL ARTERIAL": 50.0,
    "HIGHWAY RAMP": 35.0,
    "RAMP": 35.0,
    "PRIMARY": 45.0,
    "SECONDARY": 35.0,
    "RURAL COLLECTOR": 35.0,
    "URBAN ARTERIAL": 35.0,
    "URBAN COLLECTOR": 30.0,
    "URBAN MAJOR": 35.0,
    "URBAN MEDIUM": 30.0,
    "URBAN MINOR": 25.0,
    "LOCAL": 25.0,
    "PRIVATE": 15.0,
    "SERVICE DRIVE": 15.0,
    "ALLEY": 10.0,
    "TRAIL": 5.0,
    "TRAFFIC CIRCLE": 20.0,
}


@dataclass(frozen=True)
class Direction:
    forward: bool
    reverse: bool
    code: str
    known: bool


class UnionFind:
    """Small union-find implementation used to consolidate road endpoints."""

    def __init__(self, size: int) -> None:
        self.parent = np.arange(size, dtype=np.int64)
        self.rank = np.zeros(size, dtype=np.int8)

    def find(self, item: int) -> int:
        parent = self.parent
        root = item
        while parent[root] != root:
            root = int(parent[root])
        while parent[item] != item:
            next_item = int(parent[item])
            parent[item] = root
            item = next_item
        return root

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        rank = self.rank
        if rank[root_left] < rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if rank[root_left] == rank[root_right]:
            rank[root_left] += 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roads", type=Path, required=True)
    parser.add_argument("--addresses", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        metavar=("MIN_LON", "MIN_LAT", "MAX_LON", "MAX_LAT"),
        help="Optional EPSG:4326 input filter.",
    )
    parser.add_argument(
        "--projected-crs",
        default=None,
        help="Metric CRS for topology work. Default: estimated local UTM.",
    )
    parser.add_argument(
        "--endpoint-snap-tolerance-m",
        type=float,
        default=0.5,
        help="Merge road endpoints within this distance (default: 0.5 m).",
    )
    parser.add_argument(
        "--connector-merge-tolerance-m",
        type=float,
        default=0.5,
        help="Share road connector nodes for nearby addresses (default: 0.5 m).",
    )
    parser.add_argument(
        "--max-address-distance-m",
        type=float,
        default=500.0,
        help="Reject addresses farther from a centerline; <=0 disables (default: 500 m).",
    )
    parser.add_argument(
        "--unknown-oneway",
        choices=("both", "forward", "skip", "error"),
        default="both",
        help="Policy for blank/unrecognized oneway values (default: both).",
    )
    parser.add_argument(
        "--default-speed-mph",
        type=float,
        default=25.0,
        help="Fallback when speedlimit and roadclass are unusable.",
    )
    parser.add_argument(
        "--access-speed-kph",
        type=float,
        default=5.0,
        help="Speed assigned to address-access connectors (default: 5 km/h).",
    )
    parser.add_argument(
        "--address-limit",
        type=int,
        default=None,
        help="Optional deterministic limit for a quick test build.",
    )
    parser.add_argument(
        "--skip-geopackage",
        action="store_true",
        help="Only write GraphML and tabular reports.",
    )
    return parser.parse_args()


def clean_string(value: Any, default: str = "") -> str:
    if value is None or pd.isna(value):
        return default
    return str(value).strip()


def clean_number(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def native_scalar(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    return value


def read_layers(
    roads_path: Path,
    addresses_path: Path,
    bbox: tuple[float, float, float, float] | None,
    address_limit: int | None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, dict[str, Any]]:
    LOGGER.info("Reading road centerlines")
    roads = gpd.read_file(
        roads_path,
        columns=ROAD_COLUMNS,
        bbox=bbox,
        engine="pyogrio",
    )
    LOGGER.info("Reading address points")
    addresses = gpd.read_file(
        addresses_path,
        columns=ADDRESS_COLUMNS,
        bbox=bbox,
        engine="pyogrio",
    )

    if roads.crs is None or addresses.crs is None:
        raise ValueError("Both input layers must declare a CRS.")

    addresses = addresses.loc[
        addresses.geometry.notna() & ~addresses.geometry.is_empty
    ].copy()
    roads = roads.loc[roads.geometry.notna() & ~roads.geometry.is_empty].copy()

    if not roads.geometry.is_valid.all():
        roads.geometry = roads.geometry.make_valid()

    original_road_count = len(roads)
    roads["source_objectid"] = roads["OBJECTID"]
    roads = roads.explode(index_parts=True).reset_index(
        names=["source_row", "source_part"]
    )
    roads = roads.loc[roads.geometry.geom_type == "LineString"].copy()
    roads.reset_index(drop=True, inplace=True)
    roads["road_idx"] = np.arange(len(roads), dtype=np.int64)

    addresses.reset_index(drop=True, inplace=True)
    if address_limit is not None:
        addresses = addresses.iloc[:address_limit].copy()
    addresses["address_row"] = np.arange(len(addresses), dtype=np.int64)
    addresses["source_lon"] = addresses.geometry.x
    addresses["source_lat"] = addresses.geometry.y

    info = {
        "source_road_features": int(original_road_count),
        "usable_road_parts": len(roads),
        "usable_address_points": len(addresses),
        "roads_source_crs": str(roads.crs),
        "addresses_source_crs": str(addresses.crs),
    }
    return roads, addresses, info


def project_layers(
    roads: gpd.GeoDataFrame,
    addresses: gpd.GeoDataFrame,
    projected_crs: str | None,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, str]:
    target_crs = projected_crs or roads.estimate_utm_crs()
    if target_crs is None:
        raise ValueError("Could not estimate a projected CRS; pass --projected-crs.")
    roads_projected = roads.to_crs(target_crs)
    addresses_projected = addresses.to_crs(target_crs)
    return roads_projected, addresses_projected, str(roads_projected.crs)


def cluster_road_endpoints(
    roads: gpd.GeoDataFrame,
    tolerance_m: float,
) -> tuple[np.ndarray, dict[int, dict[str, Any]]]:
    if tolerance_m < 0:
        raise ValueError("Endpoint snap tolerance must be non-negative.")

    coordinates = np.empty((len(roads) * 2, 2), dtype=float)
    for road_idx, geometry in enumerate(roads.geometry):
        coords = geometry.coords
        coordinates[2 * road_idx] = coords[0][:2]
        coordinates[2 * road_idx + 1] = coords[-1][:2]

    union_find = UnionFind(len(coordinates))
    if tolerance_m > 0:
        endpoint_points = shapely.points(coordinates[:, 0], coordinates[:, 1])
        pairs = STRtree(endpoint_points).query(
            endpoint_points,
            predicate="dwithin",
            distance=tolerance_m,
        )
        for left, right in zip(pairs[0], pairs[1]):
            if left < right:
                union_find.union(int(left), int(right))

    clusters: dict[int, list[int]] = defaultdict(list)
    for endpoint_index in range(len(coordinates)):
        clusters[union_find.find(endpoint_index)].append(endpoint_index)

    root_to_node: dict[int, int] = {}
    nodes: dict[int, dict[str, Any]] = {}
    for node_id, (root, members) in enumerate(clusters.items()):
        xy = coordinates[members].mean(axis=0)
        root_to_node[root] = node_id
        nodes[node_id] = {
            "node_type": "junction",
            "x": float(xy[0]),
            "y": float(xy[1]),
            "street_count": 0,
            "geometry": Point(float(xy[0]), float(xy[1])),
        }

    endpoint_node_ids = np.empty((len(roads), 2), dtype=np.int64)
    for road_idx in range(len(roads)):
        endpoint_node_ids[road_idx, 0] = root_to_node[union_find.find(2 * road_idx)]
        endpoint_node_ids[road_idx, 1] = root_to_node[union_find.find(2 * road_idx + 1)]

    return endpoint_node_ids, nodes


def diagnose_centerline_intersections(
    roads: gpd.GeoDataFrame,
    endpoint_tolerance_m: float,
) -> dict[str, int]:
    """Report crossings that are not endpoints of one or both centerlines.

    Such crossings are deliberately not connected. They may be topology errors,
    but they can also be legitimate bridges or overpasses and this source layer
    has no grade-separation field with which to distinguish the two cases.
    """
    geometries = roads.geometry.array
    pairs = STRtree(geometries).query(geometries, predicate="intersects")
    unique = pairs[0] < pairs[1]
    left = pairs[0][unique]
    right = pairs[1][unique]
    intersections = shapely.intersection(
        geometries.take(left),
        geometries.take(right),
    )
    geometry_types = shapely.get_type_id(intersections)
    point_mask = geometry_types == 0
    left_lines = geometries.take(left[point_mask])
    right_lines = geometries.take(right[point_mask])
    points = intersections[point_mask]

    left_distance = np.minimum(
        shapely.distance(shapely.get_point(left_lines, 0), points),
        shapely.distance(shapely.get_point(left_lines, -1), points),
    )
    right_distance = np.minimum(
        shapely.distance(shapely.get_point(right_lines, 0), points),
        shapely.distance(shapely.get_point(right_lines, -1), points),
    )
    left_interior = left_distance > endpoint_tolerance_m
    right_interior = right_distance > endpoint_tolerance_m

    return {
        "intersecting_centerline_pairs": len(left),
        "point_intersection_pairs": int(point_mask.sum()),
        "nonpoint_intersection_pairs": int((~point_mask).sum()),
        "interior_to_either_line_pairs": int((left_interior | right_interior).sum()),
        "interior_to_both_lines_pairs": int((left_interior & right_interior).sum()),
    }


def match_addresses_to_roads(
    addresses: gpd.GeoDataFrame,
    roads: gpd.GeoDataFrame,
    max_distance_m: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    LOGGER.info("Matching %s addresses to nearest centerlines", f"{len(addresses):,}")
    address_points = addresses[["address_row", "geometry"]].copy()
    road_lines = roads[["road_idx", "geometry"]].copy()
    road_lines.set_index("road_idx", inplace=True, drop=False)

    joined = gpd.sjoin_nearest(
        address_points,
        road_lines[["geometry"]],
        how="left",
        distance_col="snap_distance_m",
    )
    joined.rename(columns={"index_right": "road_idx"}, inplace=True)
    joined.sort_values(
        ["address_row", "snap_distance_m", "road_idx"],
        inplace=True,
        kind="stable",
    )
    joined.drop_duplicates("address_row", keep="first", inplace=True)

    invalid = joined["road_idx"].isna()
    if max_distance_m > 0:
        invalid |= joined["snap_distance_m"] > max_distance_m

    unmatched = joined.loc[invalid, ["address_row", "snap_distance_m"]].copy()
    matched = joined.loc[~invalid].copy()
    matched["road_idx"] = matched["road_idx"].astype(np.int64)

    road_geometry = roads.geometry.array.take(matched["road_idx"].to_numpy())
    address_geometry = matched.geometry.array
    measures = shapely.line_locate_point(road_geometry, address_geometry)
    snapped_points = shapely.line_interpolate_point(road_geometry, measures)
    matched["measure_m"] = np.asarray(measures, dtype=float)
    matched["snapped_geometry"] = list(snapped_points)

    return matched, unmatched


def interpret_direction(value: Any, unknown_policy: str) -> Direction:
    code = clean_string(value).upper()
    if code == "B":
        return Direction(True, True, code, True)
    if code == "FT":
        return Direction(True, False, code, True)
    if code == "TF":
        return Direction(False, True, code, True)

    unknown_code = code or "UNKNOWN"
    if unknown_policy == "both":
        return Direction(True, True, unknown_code, False)
    if unknown_policy == "forward":
        return Direction(True, False, unknown_code, False)
    if unknown_policy == "skip":
        return Direction(False, False, unknown_code, False)
    raise ValueError(f"Unknown oneway value: {value!r}")


def choose_speed_mph(row: pd.Series, default_speed_mph: float) -> tuple[float, str]:
    speed = row.get("speedlimit")
    if speed is not None and not pd.isna(speed):
        speed = float(speed)
        if 5.0 <= speed <= 90.0:
            return speed, "speedlimit"

    road_class = clean_string(row.get("roadclass")).upper()
    if road_class in ROAD_CLASS_SPEED_MPH:
        return ROAD_CLASS_SPEED_MPH[road_class], "roadclass_default"
    return default_speed_mph, "global_default"


def reverse_linestring(geometry: LineString) -> LineString:
    return LineString(list(geometry.coords)[::-1])


def align_segment_endpoints(
    geometry: LineString,
    start_xy: tuple[float, float],
    end_xy: tuple[float, float],
) -> LineString:
    coords = list(geometry.coords)
    if len(coords) < 2:
        return LineString([start_xy, end_xy])
    coords[0] = start_xy
    coords[-1] = end_xy
    return LineString(coords)


def cluster_measures(
    assignments: pd.DataFrame,
    road_length: float,
    tolerance_m: float,
) -> tuple[list[tuple[float, list[int]]], dict[int, str]]:
    """Cluster address projections and label endpoint assignments."""
    internal: list[tuple[float, int]] = []
    endpoint_assignment: dict[int, str] = {}

    for record in assignments.itertuples(index=False):
        measure = min(max(float(record.measure_m), 0.0), road_length)
        address_row = int(record.address_row)
        if measure <= tolerance_m:
            endpoint_assignment[address_row] = "start"
        elif road_length - measure <= tolerance_m:
            endpoint_assignment[address_row] = "end"
        else:
            internal.append((measure, address_row))

    internal.sort(key=lambda item: (item[0], item[1]))
    clusters: list[list[tuple[float, int]]] = []
    for item in internal:
        if not clusters or item[0] - clusters[-1][-1][0] > tolerance_m:
            clusters.append([item])
        else:
            clusters[-1].append(item)

    result: list[tuple[float, list[int]]] = []
    for cluster in clusters:
        representative = float(np.mean([item[0] for item in cluster]))
        result.append((representative, [item[1] for item in cluster]))
    return result, endpoint_assignment


def add_directed_edge(
    edge_rows: list[dict[str, Any]],
    edge_keys: defaultdict[tuple[int, int], int],
    u: int,
    v: int,
    geometry: LineString,
    attributes: dict[str, Any],
) -> None:
    key = edge_keys[(u, v)]
    edge_keys[(u, v)] += 1
    edge_rows.append(
        {
            "u": int(u),
            "v": int(v),
            "key": int(key),
            "geometry": geometry,
            **attributes,
        }
    )


def build_graph_tables(
    roads: gpd.GeoDataFrame,
    addresses: gpd.GeoDataFrame,
    matched_addresses: pd.DataFrame,
    endpoint_node_ids: np.ndarray,
    nodes: dict[int, dict[str, Any]],
    unknown_oneway: str,
    connector_merge_tolerance_m: float,
    default_speed_mph: float,
    access_speed_kph: float,
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, pd.DataFrame, dict[str, Any]]:
    next_node_id = len(nodes)
    edge_rows: list[dict[str, Any]] = []
    edge_keys: defaultdict[tuple[int, int], int] = defaultdict(int)
    road_neighbors: defaultdict[int, set[int]] = defaultdict(set)
    address_to_road_node: dict[int, int] = {}
    direction_counts: Counter[str] = Counter()
    speed_source_counts: Counter[str] = Counter()
    road_segments_created = 0
    skipped_zero_length = 0

    grouped_assignments = {
        int(road_idx): group[["address_row", "measure_m"]].copy()
        for road_idx, group in matched_addresses.groupby("road_idx", sort=False)
    }

    LOGGER.info("Splitting roads and constructing directed edges")
    for road_position, row in roads.iterrows():
        road_idx = int(row["road_idx"])
        geometry: LineString = row.geometry
        road_length = float(geometry.length)
        if road_length <= 0:
            skipped_zero_length += 1
            continue

        start_node = int(endpoint_node_ids[road_idx, 0])
        end_node = int(endpoint_node_ids[road_idx, 1])
        assignments = grouped_assignments.get(road_idx)
        internal_clusters: list[tuple[float, list[int]]] = []
        endpoint_assignments: dict[int, str] = {}
        if assignments is not None:
            internal_clusters, endpoint_assignments = cluster_measures(
                assignments,
                road_length,
                connector_merge_tolerance_m,
            )

        for address_row, endpoint in endpoint_assignments.items():
            address_to_road_node[address_row] = (
                start_node if endpoint == "start" else end_node
            )

        split_nodes: list[tuple[float, int]] = [(0.0, start_node)]
        for measure, address_rows in internal_clusters:
            point = geometry.interpolate(measure)
            connector_node = next_node_id
            next_node_id += 1
            nodes[connector_node] = {
                "node_type": "road_connector",
                "x": float(point.x),
                "y": float(point.y),
                "street_count": 2,
                "geometry": point,
            }
            split_nodes.append((measure, connector_node))
            for address_row in address_rows:
                address_to_road_node[address_row] = connector_node
        split_nodes.append((road_length, end_node))

        direction = interpret_direction(row.get("oneway"), unknown_oneway)
        direction_counts[direction.code] += 1
        if not direction.forward and not direction.reverse:
            continue

        speed_mph, speed_source = choose_speed_mph(row, default_speed_mph)
        speed_source_counts[speed_source] += 1
        speed_kph = speed_mph * 1.609344
        source_objectid = int(row["source_objectid"])
        source_part = int(row["source_part"])

        for (start_measure, u), (end_measure, v) in pairwise(split_nodes):
            if end_measure - start_measure <= 0.01:
                skipped_zero_length += 1
                continue
            segment = substring(geometry, start_measure, end_measure)
            if not isinstance(segment, LineString):
                skipped_zero_length += 1
                continue
            u_xy = (float(nodes[u]["x"]), float(nodes[u]["y"]))
            v_xy = (float(nodes[v]["x"]), float(nodes[v]["y"]))
            segment = align_segment_endpoints(segment, u_xy, v_xy)
            segment_length = float(segment.length)
            if segment_length <= 0.01:
                skipped_zero_length += 1
                continue

            common = {
                "edge_type": "road",
                "source_objectid": source_objectid,
                "source_part": source_part,
                "road_name": clean_string(row.get("fullrdname")),
                "road_class": clean_string(row.get("roadclass")),
                "oneway_code": direction.code,
                "oneway_known": bool(direction.known),
                "speed_source": speed_source,
                "speed_mph": float(speed_mph),
                "speed_kph": float(speed_kph),
                "length": segment_length,
            }
            if direction.forward:
                add_directed_edge(
                    edge_rows,
                    edge_keys,
                    u,
                    v,
                    segment,
                    {**common, "oneway": not direction.reverse, "reversed": False},
                )
                road_neighbors[u].add(v)
                road_neighbors[v].add(u)
            if direction.reverse:
                add_directed_edge(
                    edge_rows,
                    edge_keys,
                    v,
                    u,
                    reverse_linestring(segment),
                    {**common, "oneway": not direction.forward, "reversed": True},
                )
                road_neighbors[u].add(v)
                road_neighbors[v].add(u)
            road_segments_created += 1

        if road_position and road_position % 2_500 == 0:
            LOGGER.info("Processed %s road parts", f"{road_position:,}")

    for node_id, neighbors in road_neighbors.items():
        nodes[node_id]["street_count"] = len(neighbors)

    LOGGER.info("Adding address destination nodes and access edges")
    address_lookup = addresses.set_index("address_row", drop=False)
    matched_lookup = matched_addresses.set_index("address_row", drop=False)
    address_map_rows: list[dict[str, Any]] = []

    for address_row in sorted(address_to_road_node):
        source = address_lookup.loc[address_row]
        match = matched_lookup.loc[address_row]
        road_node = address_to_road_node[address_row]
        road_xy = (float(nodes[road_node]["x"]), float(nodes[road_node]["y"]))
        point: Point = source.geometry
        address_node = next_node_id
        next_node_id += 1

        number = clean_number(source.get("add_number"))
        road_name = clean_string(source.get("fullrdname"))
        label = " ".join(part for part in (number, road_name) if part)
        landmark = clean_string(source.get("landmkname"))
        if not label:
            label = landmark or f"Address {int(source['OBJECTID'])}"

        nodes[address_node] = {
            "node_type": "address",
            "x": float(point.x),
            "y": float(point.y),
            "street_count": 1,
            "address_objectid": str(int(source["OBJECTID"])),
            "address": label,
            "landmark": landmark,
            "post_city": clean_string(source.get("post_comm")),
            "post_code": clean_string(source.get("post_code")),
            "geometry": point,
        }

        access_geometry = LineString([(float(point.x), float(point.y)), road_xy])
        access_length = float(access_geometry.length)
        access_attributes = {
            "edge_type": "address_access",
            "source_objectid": int(source["OBJECTID"]),
            "source_part": 0,
            "road_name": "",
            "road_class": "ADDRESS_ACCESS",
            "oneway_code": "B",
            "oneway_known": True,
            "speed_source": "access_default",
            "speed_mph": float(access_speed_kph / 1.609344),
            "speed_kph": float(access_speed_kph),
            "length": access_length,
            "oneway": False,
        }
        add_directed_edge(
            edge_rows,
            edge_keys,
            address_node,
            road_node,
            access_geometry,
            {**access_attributes, "reversed": False},
        )
        add_directed_edge(
            edge_rows,
            edge_keys,
            road_node,
            address_node,
            reverse_linestring(access_geometry),
            {**access_attributes, "reversed": True},
        )

        address_map_rows.append(
            {
                "address_objectid": int(source["OBJECTID"]),
                "address_node": address_node,
                "road_node": road_node,
                "address": label,
                "landmark": landmark,
                "longitude": float(source["source_lon"]),
                "latitude": float(source["source_lat"]),
                "snap_distance_m": float(match["snap_distance_m"]),
                "road_source_objectid": int(
                    roads.iloc[int(match["road_idx"])]["source_objectid"]
                ),
            }
        )

    nodes_gdf = gpd.GeoDataFrame.from_dict(
        nodes, orient="index", geometry="geometry", crs=roads.crs
    )
    nodes_gdf.index.name = "osmid"
    nodes_gdf["x"] = nodes_gdf.geometry.x
    nodes_gdf["y"] = nodes_gdf.geometry.y

    edges_gdf = gpd.GeoDataFrame(edge_rows, geometry="geometry", crs=roads.crs)
    edges_gdf.set_index(["u", "v", "key"], inplace=True)
    edges_gdf.sort_index(inplace=True)

    address_map = pd.DataFrame(address_map_rows)
    stats = {
        "direction_source_counts": dict(direction_counts),
        "speed_source_counts": dict(speed_source_counts),
        "road_segments_created": int(road_segments_created),
        "zero_length_segments_skipped": int(skipped_zero_length),
        "address_nodes_created": len(address_map_rows),
    }
    return nodes_gdf, edges_gdf, address_map, stats


def sanitize_graph_attributes(graph: nx.MultiDiGraph) -> None:
    """Remove nulls and convert NumPy values before GraphML serialization."""
    for _, attributes in graph.nodes(data=True):
        for key in list(attributes):
            value = attributes[key]
            if value is None or (
                not isinstance(value, (str, bytes)) and pd.isna(value)
            ):
                del attributes[key]
            elif key != "geometry":
                attributes[key] = native_scalar(value)
    for _, _, _, attributes in graph.edges(keys=True, data=True):
        for key in list(attributes):
            value = attributes[key]
            if value is None or (
                not isinstance(value, (str, bytes)) and pd.isna(value)
            ):
                del attributes[key]
            elif key != "geometry":
                attributes[key] = native_scalar(value)


def build_osmnx_graph(
    nodes_gdf: gpd.GeoDataFrame,
    edges_gdf: gpd.GeoDataFrame,
) -> nx.MultiDiGraph:
    graph = ox.convert.graph_from_gdfs(
        nodes_gdf,
        edges_gdf,
        graph_attrs={
            "crs": nodes_gdf.crs,
            "name": "Merced County directional address-road graph",
            "simplified": False,
        },
    )
    graph = ox.routing.add_edge_travel_times(graph)
    graph = ox.projection.project_graph(graph, to_crs="EPSG:4326")
    sanitize_graph_attributes(graph)
    return graph


def graph_statistics(graph: nx.MultiDiGraph) -> dict[str, Any]:
    weak_components = list(nx.weakly_connected_components(graph))
    strong_components = list(nx.strongly_connected_components(graph))
    edge_type_counts = Counter(
        attributes.get("edge_type", "unknown")
        for _, _, _, attributes in graph.edges(keys=True, data=True)
    )
    node_type_counts = Counter(
        attributes.get("node_type", "unknown")
        for _, attributes in graph.nodes(data=True)
    )
    return {
        "directed": bool(graph.is_directed()),
        "multigraph": bool(graph.is_multigraph()),
        "nodes": int(graph.number_of_nodes()),
        "directed_edges": int(graph.number_of_edges()),
        "node_type_counts": dict(node_type_counts),
        "edge_type_counts": dict(edge_type_counts),
        "weak_components": len(weak_components),
        "largest_weak_component_nodes": int(max(map(len, weak_components), default=0)),
        "strong_components": len(strong_components),
        "largest_strong_component_nodes": int(
            max(map(len, strong_components), default=0)
        ),
    }


def validate_direction_edges(graph: nx.MultiDiGraph) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for _, _, _, attributes in graph.edges(keys=True, data=True):
        if attributes.get("edge_type") != "road":
            continue
        code = attributes.get("oneway_code")
        reversed_edge = bool(attributes.get("reversed"))
        if code == "FT" and reversed_edge:
            counts["invalid_ft_reverse_edges"] += 1
        if code == "TF" and not reversed_edge:
            counts["invalid_tf_forward_edges"] += 1
        counts[f"{code}_{'reverse' if reversed_edge else 'forward'}"] += 1
    counts.setdefault("invalid_ft_reverse_edges", 0)
    counts.setdefault("invalid_tf_forward_edges", 0)
    return dict(counts)


def write_outputs(
    graph: nx.MultiDiGraph,
    address_map: pd.DataFrame,
    unmatched: pd.DataFrame,
    addresses: gpd.GeoDataFrame,
    output_dir: Path,
    report: dict[str, Any],
    skip_geopackage: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    graphml_path = output_dir / "merced_directional.graphml"
    geopackage_path = output_dir / "merced_directional.gpkg"
    address_map_path = output_dir / "address_node_map.csv"
    unmatched_path = output_dir / "unmatched_addresses.csv"
    report_path = output_dir / "build_report.json"

    LOGGER.info("Writing %s", graphml_path)
    ox.io.save_graphml(graph, filepath=graphml_path)
    if not skip_geopackage:
        LOGGER.info("Writing %s", geopackage_path)
        ox.io.save_graph_geopackage(graph, filepath=geopackage_path, directed=True)

    address_map.to_csv(address_map_path, index=False)
    if unmatched.empty:
        pd.DataFrame(
            columns=["address_objectid", "longitude", "latitude", "snap_distance_m"]
        ).to_csv(
            unmatched_path,
            index=False,
        )
    else:
        address_source = addresses.set_index("address_row")
        unmatched_output = unmatched.join(
            address_source[["OBJECTID", "source_lon", "source_lat"]],
            on="address_row",
        ).rename(
            columns={
                "OBJECTID": "address_objectid",
                "source_lon": "longitude",
                "source_lat": "latitude",
            }
        )
        unmatched_output[
            ["address_objectid", "longitude", "latitude", "snap_distance_m"]
        ].to_csv(unmatched_path, index=False)

    with report_path.open("w", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main() -> None:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if not args.roads.is_file():
        raise FileNotFoundError(args.roads)
    if not args.addresses.is_file():
        raise FileNotFoundError(args.addresses)
    if args.default_speed_mph <= 0 or args.access_speed_kph <= 0:
        raise ValueError("Speeds must be positive.")

    bbox = tuple(args.bbox) if args.bbox else None
    roads, addresses, source_stats = read_layers(
        args.roads,
        args.addresses,
        bbox,
        args.address_limit,
    )
    roads, addresses, projected_crs = project_layers(
        roads,
        addresses,
        args.projected_crs,
    )

    LOGGER.info("Using projected CRS %s", projected_crs)
    intersection_diagnostics = diagnose_centerline_intersections(
        roads,
        args.endpoint_snap_tolerance_m,
    )
    LOGGER.info(
        "Found %s centerline pairs crossing inside both lines; left unconnected for grade-separation safety",
        f"{intersection_diagnostics['interior_to_both_lines_pairs']:,}",
    )
    endpoint_node_ids, nodes = cluster_road_endpoints(
        roads,
        args.endpoint_snap_tolerance_m,
    )
    matched, unmatched = match_addresses_to_roads(
        addresses,
        roads,
        args.max_address_distance_m,
    )
    LOGGER.info(
        "Matched %s addresses; rejected %s",
        f"{len(matched):,}",
        f"{len(unmatched):,}",
    )

    nodes_gdf, edges_gdf, address_map, build_stats = build_graph_tables(
        roads,
        addresses,
        matched,
        endpoint_node_ids,
        nodes,
        args.unknown_oneway,
        args.connector_merge_tolerance_m,
        args.default_speed_mph,
        args.access_speed_kph,
    )
    graph = build_osmnx_graph(nodes_gdf, edges_gdf)

    topology_stats = graph_statistics(graph)
    direction_validation = validate_direction_edges(graph)
    if direction_validation["invalid_ft_reverse_edges"]:
        raise AssertionError("FT centerlines produced reverse edges.")
    if direction_validation["invalid_tf_forward_edges"]:
        raise AssertionError("TF centerlines produced forward edges.")

    report = {
        "inputs": {
            "roads": str(args.roads.resolve()),
            "addresses": str(args.addresses.resolve()),
            "bbox_wgs84": bbox,
        },
        "configuration": {
            "projected_crs": projected_crs,
            "endpoint_snap_tolerance_m": args.endpoint_snap_tolerance_m,
            "connector_merge_tolerance_m": args.connector_merge_tolerance_m,
            "max_address_distance_m": args.max_address_distance_m,
            "unknown_oneway_policy": args.unknown_oneway,
            "default_speed_mph": args.default_speed_mph,
            "access_speed_kph": args.access_speed_kph,
        },
        "source": source_stats,
        "centerline_intersection_diagnostics": intersection_diagnostics,
        "build": {
            **build_stats,
            "initial_junction_nodes": len(set(endpoint_node_ids.ravel())),
            "addresses_matched": len(matched),
            "addresses_unmatched": len(unmatched),
        },
        "topology": topology_stats,
        "direction_validation": direction_validation,
    }

    write_outputs(
        graph,
        address_map,
        unmatched,
        addresses,
        args.output_dir,
        report,
        args.skip_geopackage,
    )
    LOGGER.info(
        "Done: %s nodes, %s directed edges",
        f"{graph.number_of_nodes():,}",
        f"{graph.number_of_edges():,}",
    )


if __name__ == "__main__":
    main()
