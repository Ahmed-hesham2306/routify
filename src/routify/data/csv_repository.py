"""Load road network from CSV exports (locations.csv + roads.csv)."""

from __future__ import annotations

import csv
from pathlib import Path

from routify.algorithms.graph.adjacency_list import Graph, LocationVertex
from routify.data.hash_table import HashTable
from routify.domain.exceptions import GraphLoadError
from routify.infrastructure.logging_config import setup_logging

log = setup_logging()

#---------------------------------------------------------------------------
#data structure – graph loader
#---------------------------------------------------------------------------
#reads external csv files to populate the adjacency list graph and an 
#optional hash table for fast location name lookups.
#
#variables: v = number of vertices (locations), e = number of edges (roads)
#
#space complexity: o(v + e) — builds the full network in memory
#┌────────────────────────────┬───────────────────────────────┐
#│ operation                  │ time (worst)                  │
#├────────────────────────────┼───────────────────────────────┤
#│ file validation            │ o(1)                          │
#│ load locations             │ o(v)                          │
#│ load roads                 │ o(e)                          │
#│ total execution            │ o(v + e)                      │
#└────────────────────────────┴───────────────────────────────┘
#---------------------------------------------------------------------------

def load_graph_from_csv(
    locations_path: Path,
    roads_path: Path,
    *,
    use_hash_index: bool = True,
) -> tuple[Graph, HashTable | None]:
    """Build Member-1 graph and optional hash index for location names."""
    
    #throws an error if either of our required csv data files are missing.
    if not locations_path.is_file():
        raise GraphLoadError(f"Locations file not found: {locations_path}")
    if not roads_path.is_file():
        raise GraphLoadError(f"Roads file not found: {roads_path}")

    #initializes an empty road network and an optional hash table for quick name lookups.
    graph = Graph(quiet=True)
    index: HashTable | None = HashTable(1024) if use_hash_index else None

    log.info("Loading intersections from %s", locations_path.name)
    
    #reads the locations file line by line to build the network intersections.
    with open(locations_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            loc_id, name = row[0], row[1]
            
            #adds each new intersection to the main graph and optionally the search index.
            graph.add_location(loc_id, name)
            if index is not None:
                index.insert(loc_id, name)

    log.info("Loaded %d vertices", len(graph.network))

    edge_count = 0
    
    #reads the roads file to connect our previously loaded intersections together.
    with open(roads_path, encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            src, dest, travel_time = row[0], row[1], int(row[2])
            is_two_way = row[3].strip().upper() == "TRUE"
            
            #safely adds the road only if both the start and end points actually exist in our network.
            if src in graph.network and dest in graph.network:
                graph.add_road(src, dest, travel_time, is_two_way=is_two_way)
                edge_count += 2 if is_two_way else 1

    log.info("Loaded %d directed edge records", edge_count)
    return graph, index
