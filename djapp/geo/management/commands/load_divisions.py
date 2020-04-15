from django.core.management.base import BaseCommand
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.utils import LayerMapping
from ...models import DivisionSet, Division


GEOJSON_MAPPING = {
    "id": "ocdid",
    "division_set": {"slug": "type"},
    "shape": "GEOMETRY",
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        # create divisionsets
        DivisionSet.objects.get_or_create(slug="sldl")
        DivisionSet.objects.get_or_create(slug="sldu")

        filename = "data/tl_2019_01_sldl-with-ocdids.geojson"
        source = DataSource(filename)

        lm = LayerMapping(Division, source, GEOJSON_MAPPING)
        lm.save(progress=True)
