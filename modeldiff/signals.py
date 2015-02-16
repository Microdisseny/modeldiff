from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from modeldiff.models import Geomodeldiff


def register(model):
    post_delete.connect(geomodeldiff_post_delete, model)


def geomodeldiff_post_delete(sender, **kwargs):
    instance = kwargs['instance']

    self = instance
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

    diff.model_id = self.pk
    diff.action = 'delete'

    # save old values
    old_values_temp = model_to_dict(self, 
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
    
    if hasattr(self.Modeldiff, 'parent_field'):
        getattr(self, self.Modeldiff.parent_field).save()
