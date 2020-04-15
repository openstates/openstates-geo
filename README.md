## Open States district maps

Generate and upload map tiles for the state-level legislative district maps on [openstates.org](https://openstates.org/), both for [state overviews](https://openstates.org/ca/) and for [individual legislators](https://openstates.org/person/tim-ashe-4mV4UFZqI2WsxsnYXLM8Vb/).

- Source: SLDL and SLDU shapefiles from [the Census's TIGER/Line database](https://www.census.gov/geo/maps-data/data/tiger-line.html)
- Output: a single nationwide MBTiles vector tile set, uploaded to Mapbox for hosting
  - Intermediate files are also built and retained locally, stored in the `data` directory for debugging

![](tileset-screenshot.png)

### Dependencies

- Python 3 and `poetry`
- `pip install -r requirements.txt`
- GDAL 2
- `curl`
- `tippecanoe`
- `unzip`

### Running

Run `./make-tiles.sh` to create the map tiles, and upload them to Mapbox.

The `MAPBOX_ACCOUNT` name and `MAPBOX_ACCESS_TOKEN` (with upload privileges) must be set as environment variables. If not, then the upload step will be skipped.

### Running within Docker

Instead of setting up your local environment and executing `./make-tiles.sh`, you can instead run using Docker. This has the added benefit of loosely mirroring how the commands will be executed by CircleCI. Using Docker Compose will still allow you to access all intermediate files from the processing, within your local `data` directory.

Build and run with Docker Compose. Similar to running without Docker, the `MAPBOX_ACCOUNT` and `MAPBOX_ACCESS_TOKEN` must be set in your local environment.

```bash
docker-compose up make-tiles
```
