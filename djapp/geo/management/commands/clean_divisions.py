import glob
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from ...models import Division

ROOTDIR = Path(__file__).parent.parent.parent.parent.parent.absolute()


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("Checking for any divisions we should remove...")
        ocd_ids = []
        for filename in glob.glob(f"{ROOTDIR}/data/geojson/*.geojson"):
            obj = json.load(open(filename, "r"))
            ocd_ids.extend(div["properties"]["ocdid"] for div in obj["features"])
        print(f"Loaded {len(ocd_ids)} local divisions for comparison")
        if len(ocd_ids) < 1:
            raise Exception("No local divisions found")

        to_delete = [div for div in Division.objects.exclude(id__in=ocd_ids)]

        print(f"Found {len(to_delete)} divisions not stored locally")
        if len(to_delete) > len(ocd_ids):
            raise Exception("Found more objects to delete than expected objects")

        # delete command to remove old divisions
        # don't delete when there aren't any additional divisions
        if len(to_delete):
            print(f"Deleting {len(to_delete)} divisions from DB")
            Division.objects.exclude(id__in=ocd_ids).delete()
