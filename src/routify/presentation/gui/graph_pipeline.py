"""OSMnx graph loading and Folium map rendering."""

from __future__ import annotations

import re
from pathlib import Path

import folium
import networkx as nx

from routify.config import DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON, DEFAULT_ZOOM
from routify.infrastructure.paths import default_map_html_path, default_osm_path, web_vendor_dir
from routify.services.graph_bridge import prepare_osmnx_graph, resolve_endpoint

WEB_VENDOR_DIR = web_vendor_dir()


def _patch_glyphicons_font_paths() -> None:
    path = WEB_VENDOR_DIR / "bootstrap-glyphicons.css"
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    if "url('fonts/" in text or 'url("fonts/' in text:
        return
    text = text.replace("url('../fonts/", "url('fonts/").replace('url("../fonts/', 'url("fonts/')
    path.write_text(text, encoding="utf-8")


def patch_folium_html_paths(html_path: Path) -> None:
    required_local_assets = (
        "leaflet.js",
        "leaflet.css",
        "jquery.min.js",
        "bootstrap.bundle.min.js",
        "bootstrap.min.css",
        "leaflet.awesome-markers.js",
        "leaflet.awesome-markers.css",
        "leaflet.awesome.rotate.min.css",
    )
    if not all((WEB_VENDOR_DIR / name).is_file() for name in required_local_assets):
        # The public repository keeps generated/vendor files out of source
        # control. In that case Folium's original CDN links remain valid.
        return
    _patch_glyphicons_font_paths()
    path = Path(html_path)
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    replacements: list[tuple[str, str]] = [
        ("https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js", "leaflet.js"),
        ("https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css", "leaflet.css"),
        ("https://code.jquery.com/jquery-3.7.1.min.js", "jquery.min.js"),
        (
            "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js",
            "bootstrap.bundle.min.js",
        ),
        (
            "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css",
            "bootstrap.min.css",
        ),
        (
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js",
            "leaflet.awesome-markers.js",
        ),
        (
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css",
            "leaflet.awesome-markers.css",
        ),
        (
            "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap-glyphicons.css",
            "bootstrap-glyphicons.css",
        ),
        (
            "https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css",
            "leaflet.awesome.rotate.min.css",
        ),
        (
            "https://cdn.jsdelivr.net/gh/python-visualization/folium@main/folium/templates/leaflet.awesome.rotate.min.css",
            "leaflet.awesome.rotate.min.css",
        ),
    ]
    for remote, local in replacements:
        text = text.replace(remote, local)
    text = re.sub(
        r'<link rel="stylesheet" href="https://cdn\.jsdelivr\.net/npm/@fortawesome/fontawesome-free@[^"]+"/>',
        "",
        text,
    )
    path.write_text(text, encoding="utf-8")


def prepare_graph(osm_path: str | Path, *, retain_all: bool = False) -> nx.MultiDiGraph:
    path = Path(osm_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"OSM file not found: {path}")
    return prepare_osmnx_graph(str(path), retain_all=retain_all)


def _node_latlon(
    G: nx.MultiDiGraph,
    node,
    *,
    fallback: tuple[float, float] | None = None,
) -> tuple[float, float]:
    key = node
    if key not in G.nodes and str(node) in G.nodes:
        key = str(node)
    if key in G.nodes:
        data = G.nodes[key]
        return float(data["y"]), float(data["x"])
    if fallback is not None:
        return fallback
    raise KeyError(f"Node {node} not on map graph")


def _path_to_latlon_pairs(
    G: nx.MultiDiGraph,
    node_ids: list,
    *,
    coord_fallbacks: dict[str, tuple[float, float]] | None = None,
) -> list[list[float]]:
    out: list[list[float]] = []
    fallbacks = coord_fallbacks or {}
    for n in node_ids:
        key = str(n)
        fb = fallbacks.get(key)
        try:
            lat, lon = _node_latlon(G, n, fallback=fb)
        except KeyError:
            if fb is None:
                continue
            lat, lon = fb
        out.append([lat, lon])
    return out


def build_base_map_html(
    output_path: str | Path | None = None,
    *,
    use_online_basemap: bool = True,
) -> Path:
    """Empty OSM basemap — shown immediately on app launch (Google Maps style)."""
    if use_online_basemap:
        m = folium.Map(
            location=[DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON],
            zoom_start=DEFAULT_ZOOM,
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_zoom=19,
            attr='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        )
    else:
        m = folium.Map(
            location=[DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON],
            zoom_start=DEFAULT_ZOOM,
            tiles=None,
        )
    folium.LayerControl().add_to(m)
    _leaflet_zoom_top_right(m)
    out = Path(output_path) if output_path else default_map_html_path()
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    if out.parent.resolve() == WEB_VENDOR_DIR.resolve():
        patch_folium_html_paths(out)
    return out


def _pin_divicon(color_hex: str) -> folium.DivIcon:
    return folium.DivIcon(
        html=(
            f'<motionless style="width:26px;height:26px;background:{color_hex};'
            "border-radius:50% 50% 50% 0;transform:rotate(-45deg);"
            "border:3px solid #ffffff;box-shadow:0 2px 10px rgba(15,23,42,.4);"
            '"></motionless>'
        ).replace("motionless", "div"),
        icon_size=(32, 32),
        icon_anchor=(16, 30),
    )


def _leaflet_zoom_top_right(m: folium.Map) -> None:
    """Move zoom controls to the top-right (away from the nav panel on the left)."""
    m.get_root().html.add_child(
        folium.Element(
            """
            <style>
            .leaflet-top.leaflet-left { top: 12px; left: auto; right: 12px; }
            .leaflet-control-zoom { border: none !important; }
            </style>
            """
        )
    )


def build_multistop_map_html(
    G: nx.MultiDiGraph,
    *,
    stops: list[tuple[Any, str, tuple[float, float]]],
    trip_segments: list[tuple[list, str, tuple[float, float], tuple[float, float]]],
    alternative_legs: list[tuple[list, str, float, float, float, float]] | None = None,
    output_path: str | Path | None = None,
    use_online_basemap: bool = True,
) -> Path:
    """
    Map for ordered stops: (node_id, label, (lat, lon)).
    trip_segments: (path_nodes, algorithm_label, origin_latlon, dest_latlon) per leg.
    """
    from routify.data.location_catalog import PlaceOption
    from routify.presentation.gui.route_geometry import leg_polyline_on_osm

    if use_online_basemap:
        m = folium.Map(
            location=[DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON],
            zoom_start=DEFAULT_ZOOM,
            tiles="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
            max_zoom=19,
            attr='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        )
    else:
        m = folium.Map(
            location=[DEFAULT_CENTER_LAT, DEFAULT_CENTER_LON],
            zoom_start=DEFAULT_ZOOM,
            tiles=None,
        )

    for idx, (_node, label, (lat, lon)) in enumerate(stops):
        if idx == 0:
            color, tip = "#22c55e", f"Start · {label}"
        elif idx == len(stops) - 1:
            color, tip = "#1e293b", f"Destination · {label}"
        else:
            color, tip = "#f97316", f"Stop {idx} · {label}"
        folium.Marker(
            [lat, lon],
            tooltip=tip,
            icon=_pin_divicon(color),
        ).add_to(m)

    bounds_lats: list[float] = []
    bounds_lons: list[float] = []

    for _node, _label, (lat, lon) in stops:
        bounds_lats.append(lat)
        bounds_lons.append(lon)

    for path_nodes, algo_label, (ola, olo), (dla, dlo) in trip_segments:
        origin = PlaceOption(
            node_id=path_nodes[0] if path_nodes else "",
            display_name="",
            lat=ola,
            lon=olo,
            source="map",
        )
        dest = PlaceOption(
            node_id=path_nodes[-1] if path_nodes else "",
            display_name="",
            lat=dla,
            lon=dlo,
            source="map",
        )
        # Draw on OSM street geometry (csv path_nodes are for metrics only).
        line = leg_polyline_on_osm(G, origin, dest, csv_path_nodes=None)
        if len(line) >= 2:
            # Downsample line if it's extremely dense to fix slow Leaflet rendering
            if len(line) > 1500:
                step = max(1, len(line) // 750)
                line = line[::step] + [line[-1]]
            
            bounds_lats.extend(pt[0] for pt in line)
            bounds_lons.extend(pt[1] for pt in line)
            
            folium.PolyLine(
                line,
                color="#22c55e",
                weight=7,
                opacity=0.92,
                tooltip=algo_label,
            ).add_to(m)

    if alternative_legs:
        for alt_nodes, alt_label, ola, olo, dla, dlo in alternative_legs:
            if len(alt_nodes) < 2:
                continue
            origin = PlaceOption(
                node_id="", display_name="", lat=ola, lon=olo, source="map"
            )
            dest = PlaceOption(
                node_id="", display_name="", lat=dla, lon=dlo, source="map"
            )
            line = leg_polyline_on_osm(G, origin, dest, alt_nodes)
            if len(line) >= 2:
                # Downsample line if it's extremely dense to fix slow Leaflet rendering
                if len(line) > 1500:
                    step = max(1, len(line) // 750)
                    line = line[::step] + [line[-1]]
                
                bounds_lats.extend(pt[0] for pt in line)
                bounds_lons.extend(pt[1] for pt in line)
                
                folium.PolyLine(
                    line,
                    color="#dc2626",
                    weight=5,
                    opacity=0.82,
                    dash_array="10, 12",
                    tooltip=alt_label,
                ).add_to(m)

    if bounds_lats and bounds_lons:
        pad = 0.008
        m.fit_bounds(
            [
                [min(bounds_lats) - pad, min(bounds_lons) - pad],
                [max(bounds_lats) + pad, max(bounds_lons) + pad],
            ]
        )

    _leaflet_zoom_top_right(m)
    out = Path(output_path) if output_path else default_map_html_path()
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(out))
    if out.parent.resolve() == WEB_VENDOR_DIR.resolve():
        patch_folium_html_paths(out)
    return out


__all__ = [
    "build_base_map_html",
    "build_multistop_map_html",
    "default_map_html_path",
    "default_osm_path",
    "patch_folium_html_paths",
    "prepare_graph",
    "resolve_endpoint",
]
