"""
Google Maps UI: OSM map + multi-stop routing on the full road network database.
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QWidget,
)

from routify.config import DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV
from routify.data.csv_repository import load_graph_from_csv
from routify.data.location_catalog import LocationCatalog, PlaceOption
from routify.infrastructure.paths import default_osm_path
from routify.presentation.gui.google_maps_panel import GoogleMapsSearchCard
from routify.presentation.gui.graph_pipeline import (
    build_base_map_html,
    build_multistop_map_html,
    default_map_html_path,
    prepare_graph,
)
from routify.services import graph_store
from routify.services.multi_route import chain_shortest_path

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEngineSettings
except ImportError:  # pragma: no cover
    QWebEngineView = None  # type: ignore[misc, assignment]
    QWebEngineSettings = None  # type: ignore[misc, assignment]


class _DirectionsMapThread(QThread):
    done = pyqtSignal(object, str, int, float, int)
    failed = pyqtSignal(str)

    def __init__(
        self,
        *,
        stops: list[PlaceOption],
        map_html_path: Path,
        show_alternatives: bool,
    ) -> None:
        super().__init__()
        self._stops = stops
        self._out = map_html_path
        self._show_alternatives = show_alternatives

    def run(self) -> None:  # pragma: no cover
        try:
            osm = graph_store.get_osm_graph()
            route = graph_store.get_routify_graph()
            trip = chain_shortest_path(
                route,
                self._stops,
                include_alternatives=self._show_alternatives,
                optimize_order=len(self._stops) > 2,
            )
            map_stops = [
                (s.node_id, s.display_name, (s.lat, s.lon)) for s in self._stops
            ]
            trip_segments = [
                (
                    seg.path_nodes,
                    seg.algorithm_label,
                    (seg.origin.lat, seg.origin.lon),
                    (seg.destination.lat, seg.destination.lon),
                )
                for seg in trip.segments
            ]
            out = build_multistop_map_html(
                osm,
                stops=map_stops,
                trip_segments=trip_segments,
                alternative_legs=trip.alternative_legs or None,
                output_path=self._out,
                use_online_basemap=True,
            )
            label = " → ".join(s.display_name for s in self._stops)
            mins = max(1, int(trip.total_time_s // 60))
            km = trip.total_length_m / 1000.0
            self.done.emit(out, label, mins, km, len(self._stops))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))


class MapCanvas(QWidget):
    """Full-screen map with the navigation card floating on top (Google Maps style)."""

    _CARD_MARGIN = 16

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.web = QWebEngineView(self)
        self.web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        if QWebEngineSettings is not None:
            ws = self.web.settings()
            ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
            ws.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
            ws.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

        # Child overlay — avoids macOS WebEngine covering grid-layout siblings.
        self.search_card = GoogleMapsSearchCard(self)
        self.search_card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.search_card.adapt_to_viewport(1280, 800)
        self.search_card.move(self._CARD_MARGIN, self._CARD_MARGIN)
        self.search_card.show()
        self.search_card.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        self.web.setGeometry(self.rect())
        self.search_card.adapt_to_viewport(self.width(), self.height())
        self.search_card.move(self._CARD_MARGIN, self._CARD_MARGIN)
        self.search_card.raise_()


class RoutifyMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Routify")
        self.resize(1280, 800)

        self._map_html_path = default_map_html_path()
        self._route_thread: _DirectionsMapThread | None = None

        if QWebEngineView is None:
            raise RuntimeError("PyQt6-WebEngine is required.")

        self._canvas = MapCanvas()
        self.setCentralWidget(self._canvas)

        card = self._canvas.search_card
        card.directions_requested.connect(self._on_directions)
        card.swap_requested.connect(card.swap_fields)
        card.set_status("Loading road database…")
        QTimer.singleShot(100, self._start_graph_load)

    def _deferred_map_startup(self) -> None:
        self._show_osm_basemap()

    def _show_osm_basemap(self) -> None:
        try:
            self._canvas.search_card.raise_()
            out = build_base_map_html(self._map_html_path, use_online_basemap=True)
            self._canvas.web.load(QUrl.fromLocalFile(str(out)))
        except Exception as exc:  # noqa: BLE001
            self._canvas.search_card.set_status(f"Map error: {exc}")

    def _start_graph_load(self) -> None:
        path = default_osm_path()
        if not path.is_file():
            self._canvas.search_card.set_status("Road data missing — map tiles still work.")
            return
        self._canvas.search_card.go_btn.setEnabled(False)
        self._canvas.search_card.set_status("Loading full road database…")
        QApplication.processEvents()
        # Load on the main thread — QThread + 71k-node graph triggers macOS bus errors.
        QTimer.singleShot(30, self._load_graph_on_main_thread)

    def _load_graph_on_main_thread(self) -> None:
        path = default_osm_path()
        try:
            route_g = None
            mode = "OSM street network (light)"
            if graph_store.use_full_csv_database():
                route_g, _ = load_graph_from_csv(DEFAULT_LOCATIONS_CSV, DEFAULT_ROADS_CSV)
                mode = "full road database (71k+ intersections)"
            osm_g = prepare_graph(path, retain_all=False)
            catalog = LocationCatalog()
            count = catalog.build_from_graph(osm_g, route_g)
            graph_store.set_graphs(osm_g, catalog, route_g)
            self._on_graph_ready(count, mode)
        except Exception as exc:  # noqa: BLE001
            graph_store.clear()
            self._on_graph_failed(str(exc))

    def _on_graph_failed(self, message: str) -> None:
        graph_store.clear()
        self._canvas.search_card.go_btn.setEnabled(False)
        self._canvas.search_card.set_status(f"Could not load: {message[:120]}")

    def _on_graph_ready(self, place_count: int, mode: str) -> None:
        catalog = graph_store.get_catalog()
        if catalog is None:
            self._on_graph_failed("Catalog missing after load.")
            return
        self._canvas.search_card.set_place_names(catalog.display_names())
        self._canvas.search_card.go_btn.setEnabled(place_count > 0)
        self._canvas.search_card.set_status(
            f"Ready · {place_count} places · {mode} · use + for extra stops"
        )
        QTimer.singleShot(300, self._deferred_map_startup)

    def _resolve_stops(self, catalog: LocationCatalog) -> list[PlaceOption] | None:
        names = self._canvas.search_card.ordered_stop_names()
        stops: list[PlaceOption] = []
        for name in names:
            if not name:
                QMessageBox.warning(
                    self,
                    "Select locations",
                    "Choose every stop from the dropdown list.",
                )
                return None
            place = catalog.get_by_display_name(name)
            if place is None:
                QMessageBox.warning(
                    self,
                    "Unknown location",
                    f'"{name}" is not in the database. Pick from the list.',
                )
                return None
            stops.append(place)
        if len(stops) < 2:
            QMessageBox.information(self, "Directions", "Add at least a start and destination.")
            return None
        if len({s.node_id for s in stops}) < len(stops):
            QMessageBox.information(self, "Directions", "Each stop must be a different place.")
            return None
        return stops

    def _on_directions(self) -> None:
        catalog = graph_store.get_catalog()
        if catalog is None or graph_store.get_osm_graph() is None:
            QMessageBox.information(self, "Please wait", "Road database is still loading.")
            return
        if self._route_thread and self._route_thread.isRunning():
            return

        stops = self._resolve_stops(catalog)
        if stops is None:
            return

        route = graph_store.get_routify_graph()
        try:
            chain_shortest_path(
                route, stops,
                include_alternatives=False,
                optimize_order=len(stops) > 2,
            )
        except Exception:
            QMessageBox.warning(
                self,
                "No road route",
                "No drivable route through these stops on the road network.\n"
                "Try different stops or check the road database.",
            )
            return

        self._canvas.search_card.go_btn.setEnabled(False)
        self._canvas.search_card.set_status("Calculating route…")
        self._canvas.search_card.set_route_info("", visible=False)

        self._route_thread = _DirectionsMapThread(
            stops=stops,
            map_html_path=self._map_html_path,
            show_alternatives=self._canvas.search_card.chk_alternatives.isChecked(),
        )
        self._route_thread.done.connect(self._on_route_done)
        self._route_thread.failed.connect(self._on_route_failed)
        self._route_thread.finished.connect(
            lambda: self._canvas.search_card.go_btn.setEnabled(True)
        )
        self._route_thread.start()

    def _on_route_done(
        self, out: Path, label: str, mins: int, km: float, stop_count: int
    ) -> None:
        self._canvas.search_card.raise_()
        self._canvas.web.load(QUrl.fromLocalFile(str(out.resolve())))
        stops_note = f" · {stop_count} stops" if stop_count > 2 else ""
        parts = [p.strip() for p in label.split("→")]
        if len(parts) > 2:
            route_lbl = f"{html.escape(parts[0])} → … → {html.escape(parts[-1])}"
        else:
            route_lbl = html.escape(label)
        info = (
            f"<div style='font-size:15px;font-weight:600;color:#202124'>"
            f"{mins} min <span style='font-weight:400;color:#5f6368'>"
            f"({km:.1f} km){stops_note}</span></motionless>"
            f"<motionless style='margin-top:6px;color:#3c4043;font-size:13px;line-height:1.4'>"
            f"{route_lbl}</motionless>"
        ).replace("motionless", "div")
        self._canvas.search_card.set_route_info(info)
        self._canvas.search_card.set_status("Route displayed on map")

    def _on_route_failed(self, message: str) -> None:
        QMessageBox.critical(self, "Directions failed", message)
        self._canvas.search_card.set_status("Could not calculate route")
        self._show_osm_basemap()


def run_qt() -> int:
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts, True)
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = RoutifyMainWindow()
    win.show()
    app.processEvents()
    return app.exec()


def run_tk_fallback() -> int:
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    ttk.Label(root, text="Install PyQt6-WebEngine for the map UI.").pack(padx=12, pady=12)
    root.mainloop()
    return 0


def main() -> int:
    try:
        import PyQt6.QtWidgets  # noqa: F401
    except ImportError:
        return run_tk_fallback()
    if QWebEngineView is None:
        return run_tk_fallback()
    return run_qt()
