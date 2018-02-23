## Open States district maps

Generate and upload map tiles for the state-level legislative district maps on openstates.org.

### Dependencies

- Python 3
- Node.js 8
- GDAL
- `sed`
- `awk`
- `tippecanoe`

To install the Python and Node libraries, run:

```
pip install -r requirements.txt
npm install
```

### Running

Run `./make-tiles.sh` to create the map tiles, and upload them to Mapbox. The `MAPBOX_ACCOUNT` name and `MAPBOX_ACCESS_TOKEN` (with upload privileges) must be set as environment variables.
