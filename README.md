# Routify

Routify is a desktop route-planning application that calculates and visualizes shortest, fastest, alternative, and multi-stop routes using real road data.

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

## Run locally

```bash
python -m venv .venv
pip install -r requirements.txt
pip install -e .
python -m routify --gui
```

Run the tests with:

```bash
pytest
```

## What I practiced

Graph modelling, custom data structures, algorithm analysis, pathfinding, geospatial data processing, desktop UI development, and test-driven debugging.
