#!/usr/bin/env python3
"""Extract locations.csv and roads.csv from a local OSM XML extract."""

from __future__ import annotations

import csv
import math
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Default speed limit in km/h for roads without an explicit maxspeed tag
DEFAULT_SPEED_KPH = 40.0


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres between two lat/lon points."""
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def process_osm_xml(filename: Path) -> None:
    print(f"Reading {filename}...")
    tree = ET.parse(filename)
    root = tree.getroot()

    # Build a coordinate lookup for all <node> elements first
    node_coords: dict[str, tuple[float, float]] = {}
    for node in root.findall("node"):
        nid = node.attrib.get("id")
        lat = node.attrib.get("lat")
        lon = node.attrib.get("lon")
        if nid and lat and lon:
            node_coords[nid] = (float(lat), float(lon))

    edges_to_write: list[list] = []
    used_nodes: set[str] = set()

    for way in root.findall("way"):
        is_highway = False
        is_two_way = True
        speed_kph = DEFAULT_SPEED_KPH
        for tag in way.findall("tag"):
            k, v = tag.attrib.get("k"), tag.attrib.get("v")
            if k == "highway" and v not in ("footway", "pedestrian", "path"):
                is_highway = True
            if k == "oneway" and v == "yes":
                is_two_way = False
            if k == "maxspeed":
                try:
                    speed_kph = float(v.replace("km/h", "").strip())
                except ValueError:
                    pass
        if not is_highway:
            continue
        nodes_in_way = [nd.attrib["ref"] for nd in way.findall("nd")]
        speed_mps = speed_kph / 3.6  # convert km/h to m/s
        for i in range(len(nodes_in_way) - 1):
            src, dest = nodes_in_way[i], nodes_in_way[i + 1]
            # Compute real distance from coordinates, then derive travel time
            if src in node_coords and dest in node_coords:
                lat1, lon1 = node_coords[src]
                lat2, lon2 = node_coords[dest]
                dist_m = _haversine_m(lat1, lon1, lat2, lon2)
                travel_time = max(1, int(round(dist_m / speed_mps)))
            else:
                dist_m = 0.0
                travel_time = 1
            edges_to_write.append([src, dest, travel_time, is_two_way])
            used_nodes.update((src, dest))

    loc_path = DATA / "locations.csv"
    road_path = DATA / "roads.csv"
    DATA.mkdir(parents=True, exist_ok=True)

    with open(loc_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["location_id", "name"])
        for node_id in sorted(used_nodes, key=int):
            w.writerow([node_id, f"Intersection_{node_id}"])

    with open(road_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["source_id", "dest_id", "travel_time", "is_two_way"])
        w.writerows(edges_to_write)

    print(f"Wrote {len(used_nodes):,} locations → {loc_path}")
    print(f"Wrote {len(edges_to_write):,} edges → {road_path}")


if __name__ == "__main__":
    osm = Path(sys.argv[1]) if len(sys.argv) > 1 else DATA / "export.osm"
    process_osm_xml(osm.resolve())
