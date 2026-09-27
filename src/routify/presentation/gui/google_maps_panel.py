"""Google Maps–style directions card (responsive, QLineEdit pickers)."""

from __future__ import annotations

from PyQt6.QtCore import Qt, QStringListModel, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from routify.presentation.gui.sidebar_theme import MAPS_SEARCH_CARD_QSS


class GoogleMapsSearchCard(QFrame):
    """From / stops / To with Google Maps–style layout."""

    directions_requested = pyqtSignal()
    swap_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("searchCard")
        self.setStyleSheet(MAPS_SEARCH_CARD_QSS)
        self.setAutoFillBackground(True)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)

        self._place_model = QStringListModel()
        self._waypoint_rows: list[tuple[QWidget, QLineEdit]] = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(10)

        brand = QLabel("Routify")
        brand.setObjectName("brandLabel")
        root.addWidget(brand)
        hint = QLabel("Search the road network")
        hint.setObjectName("statusHint")
        root.addWidget(hint)

        self._inputs_block = QFrame()
        self._inputs_block.setObjectName("inputsBlock")
        block = QHBoxLayout(self._inputs_block)
        block.setContentsMargins(0, 4, 0, 4)
        block.setSpacing(10)

        self._timeline_col = QVBoxLayout()
        self._timeline_col.setSpacing(0)
        self._timeline_col.setContentsMargins(4, 8, 0, 8)
        block.addLayout(self._timeline_col)

        fields_wrap = QWidget()
        self._fields_col = QVBoxLayout(fields_wrap)
        self._fields_col.setSpacing(0)
        self._fields_col.setContentsMargins(0, 0, 0, 0)

        self.from_edit = self._make_field("Choose starting point")
        self._fields_col.addWidget(self._wrap_row(self.from_edit))

        self._waypoints_host = QVBoxLayout()
        self._waypoints_host.setSpacing(0)
        self._fields_col.addLayout(self._waypoints_host)

        self.to_edit = self._make_field("Choose destination")
        self._fields_col.addWidget(self._wrap_row(self.to_edit))

        block.addWidget(fields_wrap, stretch=1)

        self.swap_btn = QPushButton("⇅")
        self.swap_btn.setObjectName("swapButton")
        self.swap_btn.setFixedSize(36, 36)
        self.swap_btn.setToolTip("Swap start and destination")
        self.swap_btn.clicked.connect(self.swap_requested.emit)
        block.addWidget(self.swap_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

        self._inputs_scroll = QScrollArea()
        self._inputs_scroll.setWidgetResizable(True)
        self._inputs_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._inputs_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._inputs_scroll.setWidget(self._inputs_block)
        root.addWidget(self._inputs_scroll)

        self.add_stop_btn = QPushButton("+ Add stop")
        self.add_stop_btn.setObjectName("addStopButton")
        self.add_stop_btn.clicked.connect(self._on_add_stop)
        root.addWidget(self.add_stop_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        self.chk_alternatives = QCheckBox("Show alternate routes")
        self.chk_alternatives.setObjectName("altCheck")
        root.addWidget(self.chk_alternatives)

        self.go_btn = QPushButton("Directions")
        self.go_btn.setObjectName("directionsButton")
        self.go_btn.setMinimumHeight(44)
        self.go_btn.clicked.connect(self.directions_requested.emit)
        root.addWidget(self.go_btn)

        self.route_info = QLabel("")
        self.route_info.setObjectName("routeInfo")
        self.route_info.setWordWrap(True)
        self.route_info.setTextFormat(Qt.TextFormat.RichText)
        self.route_info.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum
        )
        self.route_info.setVisible(False)
        root.addWidget(self.route_info)

        self.status_label = QLabel("Loading map…")
        self.status_label.setObjectName("statusHint")
        self.status_label.setWordWrap(True)
        root.addWidget(self.status_label)

        self._rebuild_timeline()

    def _wrap_row(self, edit: QLineEdit) -> QFrame:
        row = QFrame()
        row.setObjectName("fieldRow")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 3, 0, 3)
        lay.addWidget(edit)
        return row

    def _make_field(self, placeholder: str) -> QLineEdit:
        edit = QLineEdit()
        edit.setObjectName("placeField")
        edit.setPlaceholderText(placeholder)
        edit.setMinimumHeight(40)
        edit.setClearButtonEnabled(True)
        comp = QCompleter(self._place_model, edit)
        comp.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        comp.setFilterMode(Qt.MatchFlag.MatchContains)
        comp.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        edit.setCompleter(comp)
        return edit

    def _rebuild_timeline(self) -> None:
        while self._timeline_col.count():
            item = self._timeline_col.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        stops = 2 + len(self._waypoint_rows)
        for i in range(stops):
            if i == 0:
                dot = QLabel("●")
                dot.setObjectName("fromDot")
            elif i == stops - 1:
                dot = QLabel("▲")
                dot.setObjectName("toPin")
            else:
                dot = QLabel("●")
                dot.setObjectName("waypointPin")
            dot.setFixedWidth(14)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._timeline_col.addWidget(dot, alignment=Qt.AlignmentFlag.AlignHCenter)
            if i < stops - 1:
                line = QFrame()
                line.setObjectName("timelineLine")
                line.setFixedWidth(2)
                line.setMinimumHeight(14)
                line.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
                self._timeline_col.addWidget(line, stretch=1)

    def _on_add_stop(self) -> None:
        row = QFrame()
        row.setObjectName("fieldRow")
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 3, 0, 3)
        edit = self._make_field("Add stop")
        remove_btn = QPushButton("×")
        remove_btn.setObjectName("removeStopButton")
        remove_btn.setFixedSize(28, 28)
        remove_btn.clicked.connect(lambda: self._remove_waypoint(row))
        lay.addWidget(edit, stretch=1)
        lay.addWidget(remove_btn)
        self._waypoint_rows.append((row, edit))
        self._waypoints_host.addWidget(row)
        self._rebuild_timeline()

    def _remove_waypoint(self, frame: QFrame) -> None:
        for i, (f, _edit) in enumerate(self._waypoint_rows):
            if f is frame:
                self._waypoint_rows.pop(i)
                self._waypoints_host.removeWidget(frame)
                frame.deleteLater()
                self._rebuild_timeline()
                break

    def set_place_names(self, names: list[str]) -> None:
        self._place_model.setStringList(names)
        if len(names) >= 2:
            from_i = next((i for i, n in enumerate(names) if "AUC" in n), 0)
            to_i = next(
                (i for i, n in enumerate(names) if "Cairo Festival" in n),
                1 if from_i != 1 else min(2, len(names) - 1),
            )
            self.from_edit.setText(names[from_i])
            self.to_edit.setText(names[to_i])
        elif len(names) == 1:
            self.from_edit.setText(names[0])
            self.to_edit.setText(names[0])

    def ordered_stop_names(self) -> list[str]:
        names = [self.from_edit.text().strip()]
        for _, edit in self._waypoint_rows:
            t = edit.text().strip()
            if t:
                names.append(t)
        names.append(self.to_edit.text().strip())
        return names

    def selected_from_name(self) -> str:
        return self.from_edit.text().strip()

    def selected_to_name(self) -> str:
        return self.to_edit.text().strip()

    def swap_fields(self) -> None:
        waypoint_texts = [e.text() for _, e in self._waypoint_rows]
        self._waypoint_rows.clear()
        while self._waypoints_host.count():
            item = self._waypoints_host.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        from_t, to_t = self.from_edit.text(), self.to_edit.text()
        self.from_edit.setText(to_t)
        self.to_edit.setText(from_t)
        for text in reversed(waypoint_texts):
            self._on_add_stop()
            self._waypoint_rows[-1][1].setText(text)
        self._rebuild_timeline()

    def set_route_info(self, text: str, *, visible: bool = True) -> None:
        self.route_info.setText(text)
        show = visible and bool(text)
        self.route_info.setVisible(show)
        if show:
            self.route_info.adjustSize()
            self.adjustSize()

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def adapt_to_viewport(self, width: int, height: int) -> None:
        card_w = min(400, max(320, int(width * 0.36)))
        self.setFixedWidth(card_w)
        scroll_cap = max(100, min(200, int(height * 0.26)))
        self._inputs_scroll.setMaximumHeight(scroll_cap)
        self.updateGeometry()
        self.adjustSize()
