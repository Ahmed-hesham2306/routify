# Routify

Routify is a desktop route-planning application that calculates and visualizes shortest, fastest, alternative, and multi-stop routes using real road data.

[Download the project as a ZIP](https://github.com/Ahmed-hesham2306/routify/archive/refs/heads/main.zip) · [Browse the source code](https://github.com/Ahmed-hesham2306/routify)

## Highlights

- Dijkstra and A* pathfinding
- BFS and DFS graph exploration
- Multi-stop route planning and stop-order optimization
- Alternative route generation and comparison
- Interactive OpenStreetMap view with distance and estimated travel time
- Custom graph, min-heap, hash-table, sorting, search, and AVL-tree implementations

## Tech stack

- Python
- PyQt6 and Qt WebEngine
- NetworkX and OSMnx
- Folium and Leaflet
- OpenStreetMap data

## Project structure

```text
src/routify/algorithms/     Custom data structures and algorithms
src/routify/data/           CSV and map-data access
src/routify/services/       Routing and multi-route logic
src/routify/presentation/   Desktop GUI and CLI
data/                       Sample Cairo road network data
tests/                      Algorithm and route tests
```

## Requirements

- Python 3.11 or newer
- Internet access for Python packages, OpenStreetMap tiles, and optional geocoding
- An OpenStreetMap XML export for the area you want to route through

## Download and run

1. Download the ZIP above and extract it, or clone the repository:

```bash
git clone https://github.com/Ahmed-hesham2306/routify.git
cd routify
```

2. Create a virtual environment and install the application:

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Then install the dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

3. Export a small area from [OpenStreetMap](https://www.openstreetmap.org/export), save it as `data/export.osm`, and build the local routing CSV files:

```bash
python scripts/process_osm.py data/export.osm
```

4. Start Routify:

```bash
python -m routify --gui
```

Run the automated tests with:

```bash
pytest
```

Large generated map files are intentionally not stored in the repository. This keeps the download small and lets visitors use their own OpenStreetMap area.

## What I practiced

Graph modelling, custom data structures, algorithm analysis, pathfinding, geospatial data processing, desktop UI development, and test-driven debugging.
