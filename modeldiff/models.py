from django.contrib.gis.db import models
from django.forms.models import model_to_dict
from django.contrib.gis.utils.wkt import precision_wkt
from django.utils import timezone
from django.conf import settings

from modeldiff.request import GlobalRequest

import json
import datetime


class ModeldiffMixin(models.Model):
    """
    Base model to save the changes to a model
    """
    date_created = models.DateTimeField(default=timezone.now)
    # optional key identifying the source
    key = models.CharField(max_length=20, blank=True, default='',
                           db_index=True)
    key_id = models.IntegerField(blank=True, null=True)
    username = models.CharField(max_length=50, default='', blank=True)
    model_name = models.CharField(max_length=50)
    model_id = models.IntegerField(blank=True, null=True)
    # model unique identifier
    unique_id = models.CharField(max_length=50, default='', blank=True)
    action = models.CharField(max_length=6)
    old_data = models.TextField()
    new_data = models.TextField()
    applied = models.BooleanField(default=False, db_index=True)

    class Meta:
        abstract = True


class Modeldiff(ModeldiffMixin, models.Model):
    pass


class Geomodeldiff(ModeldiffMixin, models.Model):
    the_geom = models.GeometryField(srid=4326, null=True, blank=True)
    objects = models.GeoManager()


class SaveModeldiffMixin(models.Model):
    """
    Use real=True to access the real save function
    otherwise the Modeldiff logic will apply
    """
    def save(self, *args, **kwargs):
        # see if we need to save the object (real = True)
        # or should generate a Modeldiff (real = False)
        ignore = kwargs.get('modeldiff_ignore', False)

        if ignore:
            # call original handler
            kwargs.pop('modeldiff_ignore')
            super(SaveModeldiffMixin, self).save(*args, **kwargs)
            return

        fields = self.Modeldiff.fields

        diff = Modeldiff()
        diff.model_name = self.Modeldiff.model_name
        diff.key = settings.MODELDIFF_KEY
        if hasattr(self, 'username'):
            diff.username = self.username
        else:
            try:
                diff.username = GlobalRequest().user.username
            except:
                pass

        unique_field = getattr(self.Modeldiff, 'unique_field', None)
        if unique_field:
            diff.unique_id = getattr(self, unique_field)

        if self.pk:
            diff.model_id = self.pk
            diff.action = 'update'
            # get original object in database
            original = self.__class__.objects.get(pk=self.pk)

            # compare original and current (self)
            old_values = {}
            new_values = {}
            old_values_temp = model_to_dict(original, 
                                            fields=self.Modeldiff.fields)
            new_values_temp = model_to_dict(self, fields=self.Modeldiff.fields)
            
            for k in fields:
                old_value = old_values_temp[k]
                new_value = new_values_temp[k]
                
                #Override DateField and DateTimeField
                if isinstance(new_value, datetime.datetime):
                    new_value = new_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime("%Y-%m-%d")
                
                if isinstance(old_value, datetime.datetime):
                    old_value = old_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime("%Y-%m-%d")
                
                old_values[k] = old_value
                
                if old_value != new_value:
                    new_values[k] = new_value

            diff.old_data = json.dumps(old_values)
            diff.new_data = json.dumps(new_values)
            diff.save()
        else:
            diff.action = 'add'
            # save all new values

            new_values_temp = model_to_dict(self, fields=self.Modeldiff.fields)
            new_values = {}
            
            for k in fields:
                new_value = new_values_temp[k]
                
                #Override DateField and DateTimeField
                if isinstance(new_value, datetime.datetime):
                    new_value = new_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime("%Y-%m-%d")       
                        
                new_values[k] = new_value
                
            diff.new_data = json.dumps(new_values)
            diff.save()

        super(SaveModeldiffMixin, self).save(*args, **kwargs)
        if diff.model_id is None and self.pk:
            diff.model_id = self.pk
            diff.save()

        if hasattr(self.Modeldiff, 'parent_field'):
            getattr(self, self.Modeldiff.parent_field).save()      

    # this is best handled using signals
    def delete_deprecated(self, *args, **kwargs):
        real = kwargs.get('real', False)

        if real:
            # call original handler
            kwargs.pop('real')
            super(SaveModeldiffMixin, self).delete(*args, **kwargs)
            return

        fields = self.Modeldiff.fields


        diff = Modeldiff()
        diff.model_name = self.Modeldiff.model_name
        if hasattr(self, 'username'):
            diff.username = self.username
        else:
            try:
                diff.username = GlobalRequest().user.username
            except:
                pass

        if self.pk:
            diff.model_id = self.pk
            diff.action = 'delete'
            # get original object in database
            original = self.__class__.objects.get(pk=self.pk)

            # save old values
            old_values_temp = model_to_dict(original, 
                                            fields=self.Modeldiff.fields)
            old_values = {}
            
            for k in fields:
                old_value = old_values_temp[k]
                
                #Override DateField and DateTimeField
                if isinstance(old_value, datetime.datetime):
                    old_value = old_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime("%Y-%m-%d")        
                        
                old_values[k] = old_value

            diff.old_data = json.dumps(old_values)
            diff.save()

        super(SaveModeldiffMixin, self).delete(*args, **kwargs)
        
        if hasattr(self.Modeldiff, 'parent_field'):
            getattr(self, self.Modeldiff.parent_field).save()
        
    class Meta:
        abstract = True


class SaveGeomodeldiffMixin(models.Model):
    """
    Use real=True to access the real save function
    otherwise the Modeldiff logic will apply
    """
    def save(self, *args, **kwargs):
        # see if we need to save the object (real = True)
        # or should generate a Modeldiff (real = False)
        ignore = kwargs.get('modeldiff_ignore', False)

        if ignore:
            # call original handler
            kwargs.pop('modeldiff_ignore')
            super(SaveGeomodeldiffMixin, self).save(*args, **kwargs)
            return

        fields = self.Modeldiff.fields
        geom_field = self.Modeldiff.geom_field
        geom_precision = self.Modeldiff.geom_precision

        diff = Geomodeldiff()
        diff.model_name = self.Modeldiff.model_name
        diff.key = settings.MODELDIFF_KEY
        if hasattr(self, 'username'):
            diff.username = self.username
        else:
            try:
                diff.username = GlobalRequest().user.username
            except:
                pass

        unique_field = getattr(self.Modeldiff, 'unique_field', None)
        if unique_field:
            diff.unique_id = getattr(self, unique_field)

        original = None
        if self.pk:
            # get original object in database
            try:
                original = self.__class__.objects.get(pk=self.pk)
            except:
                pass

        if original:
            diff.model_id = self.pk
            diff.action = 'update'

            # compare original and current (self)
            old_values = {}
            new_values = {}
            old_values_temp = model_to_dict(original, 
                                            fields=self.Modeldiff.fields)
            new_values_temp = model_to_dict(self, 
                                            fields=self.Modeldiff.fields)
            
           
            for k in fields:
                old_value = old_values_temp[k]
                new_value = new_values_temp[k]
                
                #Override DateField and DateTimeField
                if isinstance(new_value, datetime.datetime):
                    new_value = new_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime("%Y-%m-%d")
                
                if isinstance(old_value, datetime.datetime):
                    old_value = old_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime("%Y-%m-%d")
                
                old_values[k] = old_value
                
                if old_value != new_value:
                    new_values[k] = new_value

            # save original geometry
            geom = getattr(original, geom_field)
            if geom:
                old_values[geom_field] = precision_wkt(geom, geom_precision)
            else:
                old_values[geom_field] = None

            # compare original and new geometry
            new_geom = getattr(self, geom_field)
            diff.the_geom = new_geom
            if new_geom:
                new_geom_value = precision_wkt(new_geom, geom_precision)
            else:
                new_geom_value = None

            if not new_geom_value == old_values[geom_field]:
                new_values[geom_field] = new_geom_value

            diff.old_data = json.dumps(old_values)
            diff.new_data = json.dumps(new_values)
            diff.save()
        else:
            diff.action = 'add'
            # save all new values
            new_values_temp = model_to_dict(self, fields=self.Modeldiff.fields)
            new_values = {}
            
            for k in fields:
                new_value = new_values_temp[k]
                #Override DateField and DateTimeField
                if isinstance(new_value, datetime.datetime):
                    new_value = new_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(new_value, datetime.date):
                        new_value = new_value.strftime("%Y-%m-%d")
                        
                new_values[k] = new_value

            new_geom = getattr(self, geom_field)
            diff.the_geom = new_geom
            if new_geom:
                new_values[geom_field] = precision_wkt(new_geom,
                                                       geom_precision)
            diff.new_data = json.dumps(new_values)
            diff.save()

        super(SaveGeomodeldiffMixin, self).save(*args, **kwargs)
        if diff.model_id is None and self.pk:
            diff.model_id = self.pk
            diff.save()

        if hasattr(self.Modeldiff, 'parent_field'):
            getattr(self, self.Modeldiff.parent_field).save()

    # this is best handled using signals
    def delete_deprecated(self, *args, **kwargs):
        real = kwargs.get('real', False)

        if real:
            # call original handler
            kwargs.pop('real')
            super(SaveGeomodeldiffMixin, self).delete(*args, **kwargs)
            return

        fields = self.Modeldiff.fields
        geom_field = self.Modeldiff.geom_field
        geom_precision = self.Modeldiff.geom_precision

        diff = Geomodeldiff()
        diff.model_name = self.Modeldiff.model_name
        if hasattr(self, 'username'):
            diff.username = self.username
        else:
            try:
                diff.username = GlobalRequest().user.username
            except:
                pass

        if self.pk:
            diff.model_id = self.pk
            diff.action = 'delete'
            # get original object in database
            original = self.__class__.objects.get(pk=self.pk)

            # save old values
            old_values_temp = model_to_dict(original, 
                                            fields=self.Modeldiff.fields)
            old_values = {}
            
            for k in fields:
                old_value = old_values_temp[k]
                
                #Override DateField and DateTimeField
                if isinstance(old_value, datetime.datetime):
                    old_value = old_value.strftime("%Y-%m-%d %H:%M:%S.%f%z")
                else:
                    if isinstance(old_value, datetime.date):
                        old_value = old_value.strftime("%Y-%m-%d")       
                        
                old_values[k] = old_value
                

            # save geometry
            geom = getattr(self, geom_field)
            diff.the_geom = geom
            if geom:
                old_values[geom_field] = precision_wkt(geom, geom_precision)
            else:
                old_values[geom_field] = None

            diff.old_data = json.dumps(old_values)
            diff.save()

        super(SaveGeomodeldiffMixin, self).delete(*args, **kwargs)
        
        if hasattr(self.Modeldiff, 'parent_field'):
            getattr(self, self.Modeldiff.parent_field).save()

    class Meta:
        abstract = True
