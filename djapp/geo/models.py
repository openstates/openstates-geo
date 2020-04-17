from django.contrib.gis.db import models


class DivisionSet(models.Model):
    slug = models.SlugField(max_length=50, primary_key=True)


class Division(models.Model):
    id = models.CharField(max_length=300, primary_key=True)
    division_set = models.ForeignKey(
        DivisionSet, on_delete=models.CASCADE, related_name="divisions"
    )
    name = models.CharField(max_length=300)
    state = models.CharField(max_length=2)
    shape = models.MultiPolygonField()
