from django.contrib.gis.db import models

from models import SaveGeomodeldiffMixin


class PersonModel(SaveGeomodeldiffMixin, models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    the_geom = models.PointField(srid=4326, null=True, blank=True)

    objects = models.GeoManager()

    class Modeldiff:
        model_name = 'modeldiff.PersonModel'
        fields = ('name', 'surname',)
        geom_field = 'the_geom'
        geom_precision = 8
