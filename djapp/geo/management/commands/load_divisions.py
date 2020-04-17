import glob
from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping, LayerMapError
from ...models import DivisionSet, Division


GEOJSON_MAPPING = {
    "id": "ocdid",
    "state": "state",
    "name": "name",
    "division_set": {"slug": "type"},
    "shape": "GEOMETRY",
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true")
        parser.add_argument("filenames", nargs="*")

    def handle(self, *args, **options):
        # create divisionsets
        DivisionSet.objects.get_or_create(slug="sldl")
        DivisionSet.objects.get_or_create(slug="sldu")

        filenames = options["filenames"] or sorted(glob.glob("data/geojson/*.geojson"))

        for filename in filenames:
            print(f"processing {filename}...")
            source = DataSource(filename)
            try:
                lm = LayerMapping(Division, source, GEOJSON_MAPPING)
            except LayerMapError:
                # this error gets triggered if the GeoJSON type is MULTIPOLYGON
                multipoly_mapping = GEOJSON_MAPPING.copy()
                multipoly_mapping["shape"] = "MULTIPOLYGON"
                lm = LayerMapping(Division, source, multipoly_mapping)
            lm.save(verbose=options["verbose"])
