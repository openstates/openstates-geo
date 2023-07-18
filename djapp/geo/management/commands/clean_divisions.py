import glob
import json
from django.core.management.base import BaseCommand
from ...models import Division

GEOJSON_MAPPING = {
    "id": "ocdid",
}


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--verbose", action="store_true")

    def handle(self, *args, **options):
        ocd_ids = []
        for filename in glob.glob("data/geojson/*.geojson"):
            obj = json.load(filename)
            ocd_ids.append(obj["ocdid"])
        print(f"Loaded {len(ocd_ids)} local divisions for comparison")

        to_delete = [div for div in Division.objects.exclude(id__in=ocd_ids)]

        print(f"Found {len(to_delete)} divisions not stored locally")

        # delete command to remove old divisions
        # Division.objects.exclude(id__in=ocd_ids).delete()
