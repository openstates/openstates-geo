## Open States district maps

[![CircleCI](https://circleci.com/gh/openstates/openstates-district-maps/tree/master.svg?style=svg)](https://circleci.com/gh/openstates/openstates-district-maps/tree/master)

Generate and upload map tiles for the state-level legislative district maps on openstates.org.

- Source: SLDL and SLDU shapefiles from the Census's TIGER/Line database
- Output: a single nationwide MBTiles vector tile set, uploaded to Mapbox for hosting
  - Intermediate files are also built locally, stored in the `data` directory for debugging and other uses

### Dependencies

- Python 3 and `pip`
- Node.js 10 and `npm`
- GDAL/OGR
- `curl`
- `gawk`
- `sed`
- `tippecanoe`
- `unzip`

To install the Python and Node libraries, run:

```bash
pip install -r requirements.txt
npm install
```

### Running

Run `./make-tiles.sh` to create the map tiles, and upload them to Mapbox.

The `MAPBOX_ACCOUNT` name and `MAPBOX_ACCESS_TOKEN` (with upload privileges) must be set as environment variables. If not, then the upload step will be skipped.

### Within Docker

Instead of setting up your local environment and running `./make-tiles.sh`, you can instead run using Docker. This has the added benefit of loosely mirroring how the commands will be executed by CircleCI. Further, using Docker Compose will allow you to easily access all files from the processing, within your local `./data` directory.

Build and run with Docker Compose. Similar to running without Docker, the `MAPBOX_ACCOUNT` and `MAPBOX_ACCESS_TOKEN` must be set in your local environment.

```bash
docker-compose up make-tiles
```

### Continuous integration

For Open States itself, CircleCI will auto-build and deploy this tileset to our Mapbox account for use in production. So, make sure to locally check any changes to the tileset before committing build changes to the `master` branch.

Note: This automated system is set up using Docker Hub auto-builds, and CircleCI to run those auto-built images. Since both processes start at the same time, _CircleCI does not run the most recent image_; it will run one auto-built from a previous commit, likely from about 20 minutes before. Circle _does_ do a fresh checkout of the Git repository, so the only problems that the Circle + Docker Hub asynchronousness causes are when the contents of the `Dockerfile` have changed; changes in the build scripts themselves will cause no issues.
