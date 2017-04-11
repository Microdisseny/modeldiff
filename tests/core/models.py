from django.contrib.gis.db import models

from modeldiff.models import SaveGeomodeldiffMixin, SaveModeldiffMixin
from modeldiff.signals import modeldiff_manager


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


class PersonPropertyModel(SaveModeldiffMixin, models.Model):
    person = models.ForeignKey(PersonModel)
    address = models.CharField(max_length=50, null=True, blank=True)

    class Modeldiff:
        model_name = 'modeldiff.PersonPropertyModel'
        fields = ('person', 'address')
        parent_field = 'person'


class PersonPropertyForGeoModel(SaveModeldiffMixin, models.Model):
    person = models.ForeignKey(PersonGeoModel)
    address = models.CharField(max_length=50, null=True, blank=True)

    class Modeldiff:
        model_name = 'modeldiff.PersonPropertyForGeoModel'
        fields = ('person', 'address')
        parent_field = 'person'


for model in (PersonModel, PersonPropertyModel, PersonPropertyForGeoModel):
    modeldiff_manager.register_modeldiff(model)

for model in (PersonGeoModel,):
    modeldiff_manager.register_geomodeldiff(model)
