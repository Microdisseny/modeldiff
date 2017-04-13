from django.contrib.gis import admin as gis_admin
from django.contrib import admin
from modeldiff.models import Modeldiff, Geomodeldiff
from leaflet.admin import LeafletGeoAdmin

from django.apps import apps


class ModeldiffAdminListFilter(admin.SimpleListFilter):
    title = 'Model'
    parameter_name = 'model_name'

    def lookups(self, request, model_admin):
        models_name = ()

        for model in apps.get_models():
            if hasattr(model, 'Modeldiff') and not hasattr(model.Modeldiff,
                                                           'geom_field'):
                models_name = models_name + ((model.Modeldiff.model_name,
                                              model.Modeldiff.model_name,),)

        return models_name

    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        else:
            return queryset.filter(model_name=self.value())


class GeomodeldiffAdminListFilter(ModeldiffAdminListFilter):

    def lookups(self, request, model_admin):
        models_name = ()

        for model in apps.get_models():
            if hasattr(model, 'Modeldiff') and hasattr(model.Modeldiff,
                                                       'geom_field'):
                models_name = models_name + ((model.Modeldiff.model_name,
                                              model.Modeldiff.model_name,),)

        return models_name


class ModeldiffAdmin(gis_admin.ModelAdmin):
    list_display = ('date_created', 'key', 'key_id', 'username', 'model_name',
                    'model_id', 'unique_id', 'action', 'applied')
    search_fields = ('username', 'model_name', '=model_id',)
    list_filter = ('applied', 'key', ModeldiffAdminListFilter,)
    date_hierarchy = 'date_created'

gis_admin.site.register(Modeldiff, ModeldiffAdmin)


class GeomodeldiffAdmin(LeafletGeoAdmin):
    list_display = ('date_created', 'key', 'key_id', 'username', 'model_name',
                    'model_id', 'unique_id', 'action', 'applied')
    search_fields = ('username', 'model_name', '=model_id',)
    list_filter = ('applied', 'key', GeomodeldiffAdminListFilter,)
    date_hierarchy = 'date_created'

gis_admin.site.register(Geomodeldiff, GeomodeldiffAdmin)
