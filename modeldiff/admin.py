from django.contrib.gis import admin
from models import Modeldiff, Geomodeldiff
from leaflet.admin import LeafletGeoAdmin


class ModeldiffAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'key', 'key_id', 'username', 'model_name',
                    'model_id', 'action', 'applied')
    search_fields = ('username', 'model_name', 'model_id',)
admin.site.register(Modeldiff, ModeldiffAdmin)


class GeomodeldiffAdmin(LeafletGeoAdmin):
    list_display = ('date_created', 'username', 'model_name', 'model_id',
                    'action', 'applied')
    search_fields = ('username', 'model_name', 'model_id',)

admin.site.register(Geomodeldiff, GeomodeldiffAdmin)
