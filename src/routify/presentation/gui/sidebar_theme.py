"""Qt styles for the Routify control panel (left sidebar)."""

MAPS_SEARCH_CARD_QSS = """
#searchCard {
    background-color: #ffffff;
    border-radius: 16px;
    border: 1px solid #e8eaed;
}
#searchCard QLabel#brandLabel {
    font-size: 22px;
    font-weight: 600;
    color: #202124;
    letter-spacing: -0.3px;
}
#searchCard QLabel#statusHint {
    font-size: 12px;
    color: #70757a;
    padding: 0;
    margin: 0;
}
#searchCard QFrame#inputsBlock {
    background: #f8f9fa;
    border-radius: 12px;
    border: 1px solid #e8eaed;
}
#searchCard QFrame#timelineLine {
    background-color: #dadce0;
    border: none;
    min-height: 12px;
    max-width: 2px;
}
#searchCard QLabel#fromDot {
    color: #34a853;
    font-size: 12px;
    font-weight: bold;
}
#searchCard QLabel#toPin {
    color: #ea4335;
    font-size: 10px;
}
#searchCard QLabel#waypointPin {
    color: #fbbc04;
    font-size: 11px;
}
#searchCard QLineEdit#placeField {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e8eaed;
    border-radius: 0;
    padding: 10px 8px;
    font-size: 14px;
    color: #202124;
    selection-background-color: #e8f0fe;
}
#searchCard QLineEdit#placeField:focus {
    border-bottom: 2px solid #1a73e8;
    padding-bottom: 9px;
}
#searchCard QFrame#fieldRow:last-child QLineEdit#placeField {
    border-bottom: none;
}
#searchCard QPushButton#swapButton {
    background: #ffffff;
    border: 1px solid #dadce0;
    border-radius: 18px;
    color: #5f6368;
    font-size: 16px;
}
#searchCard QPushButton#swapButton:hover {
    background: #f1f3f4;
    color: #202124;
}
#searchCard QPushButton#addStopButton {
    background: transparent;
    color: #1a73e8;
    border: none;
    font-size: 13px;
    font-weight: 500;
    text-align: left;
    padding: 2px 4px;
}
#searchCard QPushButton#addStopButton:hover {
    color: #174ea6;
}
#searchCard QPushButton#removeStopButton {
    background: transparent;
    border: none;
    border-radius: 14px;
    color: #70757a;
    font-size: 18px;
    font-weight: bold;
}
#searchCard QPushButton#removeStopButton:hover {
    background: #fce8e6;
    color: #d93025;
}
#searchCard QPushButton#directionsButton {
    background-color: #1a73e8;
    color: #ffffff;
    font-weight: 600;
    font-size: 15px;
    border: none;
    border-radius: 24px;
    padding: 10px 24px;
}
#searchCard QPushButton#directionsButton:hover {
    background-color: #1765cc;
    box-shadow: 0 1px 3px rgba(60,64,67,.3);
}
#searchCard QPushButton#directionsButton:pressed {
    background-color: #1557b0;
}
#searchCard QPushButton#directionsButton:disabled {
    background-color: #f1f3f4;
    color: #9aa0a6;
}
#searchCard QCheckBox#altCheck {
    font-size: 13px;
    color: #5f6368;
    spacing: 8px;
}
#searchCard QCheckBox#altCheck::indicator {
    width: 16px;
    height: 16px;
    border-radius: 2px;
    border: 2px solid #dadce0;
}
#searchCard QCheckBox#altCheck::indicator:checked {
    background: #1a73e8;
    border-color: #1a73e8;
}
#searchCard QLabel#routeInfo {
    font-size: 14px;
    line-height: 1.45;
    color: #202124;
    background-color: #e8f0fe;
    border-radius: 12px;
    padding: 14px 16px;
    margin: 0;
    min-height: 24px;
}
#searchCard QScrollArea {
    background: transparent;
    border: none;
}
"""
