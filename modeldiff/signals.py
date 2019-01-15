import datetime
import json

from django.conf import settings
from django.contrib.gis.geos import WKTWriter
from django.db.models.signals import pre_delete
from django.forms.models import model_to_dict

from modeldiff.models import Geomodeldiff, Modeldiff
from modeldiff.request import GlobalRequest


class ModeldiffManager(object):
    def register_modeldiff(self, model):
        pre_delete.connect(self.modeldiff_pre_delete, model)

    def register_geomodeldiff(self, model):
        pre_delete.connect(self.geomodeldiff_pre_delete, model)

    def modeldiff_pre_delete(self, sender, **kwargs):
        self._pre_delete(Modeldiff, sender, **kwargs)

    def geomodeldiff_pre_delete(self, sender, **kwargs):
        self._pre_delete(Geomodeldiff, sender, **kwargs)

    def _pre_delete(self, modeldiff_class, sender, **kwargs):
        instance = kwargs['instance']

        # see if we need to create a modeldiff to track the object deletion
        if hasattr(instance, '_modeldiff_ignore'):
            del instance._modeldiff_ignore
            return

        fields = sender.Modeldiff.fields

        diff = modeldiff_class()
        diff.applied = True
        diff.model_name = sender.Modeldiff.model_name
        diff.key = settings.MODELDIFF_KEY
        diff.username = self._get_username(instance)

        diff.model_id = instance.pk
        diff.action = 'delete'

        unique_field = getattr(sender.Modeldiff, 'unique_field', None)
        if unique_field:
            diff.unique_id = getattr(instance, unique_field)

        # get original object in database
        original = sender.objects.get(pk=instance.pk)

        # save old values
        old_values_temp = model_to_dict(original,
                                        fields=sender.Modeldiff.fields)
        old_values = {}

        for k in fields:
            old_value = old_values_temp[k]

            # Override DateField and DateTimeField
            if isinstance(old_value, datetime.datetime):
                old_value = old_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
            else:
                if isinstance(old_value, datetime.date):
                    old_value = old_value.strftime("%Y-%m-%d")

            old_values[k] = old_value

        if modeldiff_class == Geomodeldiff:
            geom_field = sender.Modeldiff.geom_field
            geom_precision = sender.Modeldiff.geom_precision
            wkt_w = WKTWriter(precision=geom_precision)
            # save geometry
            geom = getattr(instance, geom_field)
            diff.the_geom = geom
            if geom:
                old_values[geom_field] = wkt_w.write(geom).decode('utf8')
            else:
                old_values[geom_field] = None

        diff.old_data = json.dumps(old_values)
        diff.save()

        if hasattr(sender.Modeldiff, 'parent_field'):
            getattr(instance, sender.Modeldiff.parent_field).save()

    def _get_username(self, instance):
        if hasattr(instance, 'username'):
            return instance.username
        else:
            try:
                return GlobalRequest().user.username
            except Exception:
                return ''


modeldiff_manager = ModeldiffManager()
