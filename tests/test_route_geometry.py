"""Map polyline geometry follows OSM streets (not straight off-road lines)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pytest

from routify.data.location_catalog import LocationCatalog, PlaceOption
from routify.data.csv_repository import load_graph_from_csv
from routify.config import DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV
from routify.infrastructure.paths import default_osm_path
from routify.presentation.gui.graph_pipeline import prepare_graph
from routify.presentation.gui.route_geometry import leg_polyline_on_osm
from routify.services.multi_route import chain_shortest_path

pytestmark = pytest.mark.skipif(
    not default_osm_path().is_file(),
    reason="OSM extract required",
)


def _polyline_length_m(line: list[list[float]]) -> float:
    total = 0.0
    for i in range(len(line) - 1):
        lat1, lon1 = line[i]
        lat2, lon2 = line[i + 1]
        r = 6_371_000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlon / 2) ** 2
        total += 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return total


def _crow_flies_m(a: PlaceOption, b: PlaceOption) -> float:
    return _polyline_length_m([[a.lat, a.lon], [b.lat, b.lon]])


@pytest.fixture(scope="module")
def osm_graph():
    return prepare_graph(default_osm_path(), retain_all=False)


@pytest.fixture(scope="module")
def al_jazira_to_teseen(osm_graph):
    route_g, _ = load_graph_from_csv(DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV)
    catalog = LocationCatalog()
    catalog.build_from_graph(osm_graph, route_g)
    origin = catalog.get_by_display_name("Al_Jazira_St_S")
    dest = catalog.get_by_display_name("Al_Teseen_Lateral_W")
    assert origin is not None and dest is not None
    trip = chain_shortest_path(route_g, [origin, dest])
    return osm_graph, origin, dest, trip.segments[0].path_nodes


def test_leg_polyline_follows_streets_not_crow_flies(osm_graph, al_jazira_to_teseen):
    G, origin, dest, csv_path = al_jazira_to_teseen
    line = leg_polyline_on_osm(G, origin, dest, csv_path_nodes=csv_path)
    assert len(line) >= 8, "road-following routes should have many shape points"
    crow = _crow_flies_m(origin, dest)
    along = _polyline_length_m(line)
    assert along > crow * 1.15, "polyline should be longer than a straight off-road line"


def test_leg_polyline_ignores_csv_hops_when_osm_available(osm_graph, al_jazira_to_teseen):
    G, origin, dest, csv_path = al_jazira_to_teseen
    with_csv = leg_polyline_on_osm(G, origin, dest, csv_path_nodes=csv_path)
    osm_only = leg_polyline_on_osm(G, origin, dest, csv_path_nodes=None)
    assert len(osm_only) >= 8
    assert len(with_csv) == len(osm_only)
