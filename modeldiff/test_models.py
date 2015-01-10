from django.contrib.gis.db import models

from models import SaveGeomodeldiffMixin, SaveModeldiffMixin 


class PersonModel(SaveModeldiffMixin, models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(null=False, blank=False)

    objects = models.GeoManager()

    class Modeldiff:
        model_name = 'modeldiff.PersonModel'
        fields = ('name', 'surname', 'birthdate', 'updated_at')

        
class PersonGeoModel(SaveGeomodeldiffMixin, models.Model):
    name = models.CharField(max_length=50, null=True, blank=True)
    surname = models.CharField(max_length=50, null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(null=False, blank=False)
    the_geom = models.PointField(srid=4326, null=True, blank=True)

    objects = models.GeoManager()

    class Modeldiff:
        model_name = 'modeldiff.PersonGeoModel'
        fields = ('name', 'surname', 'birthdate', 'updated_at')
        geom_field = 'the_geom'
        geom_precision = 8
