## Open States district maps

Generate and upload the SLDL and SLDU map tiles for openstates.org.

### Dependencies

- `pip install -r requirements.txt`
- `npm install`
- `gdal`
- `tippecanoe`
- [`Mapbox CLI`](https://github.com/mapbox/mapbox-cli-py)

### Running

Run `./make-tiles.sh` to create the map tiles, and upload them to Mapbox. The `MAPBOX_ACCOUNT` name and `MAPBOX_ACCESS_TOKEN` (with upload privileges) must be set as environment variables.
