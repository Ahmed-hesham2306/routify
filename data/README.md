# Map data

Routify works with an OpenStreetMap XML export and generates its local CSV graph files from that source.

1. Export a small area from <https://www.openstreetmap.org/export>.
2. Save the file as `data/export.osm`.
3. From the repository root, run:

   ```bash
   python scripts/process_osm.py data/export.osm
   ```

This creates `data/locations.csv` and `data/roads.csv`. Generated map data is ignored by Git because it can be large and depends on the area selected by each user.
