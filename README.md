django modeldiff
================

When saving a model, store the changes in a modeldiff object so they can be applied elsewhere. Also helps tracking user's modifications

Usage
-----

Add ''modeldiff'' to INSTALLED_APPS

Run ''manage.py migrate''

Add a Modeldiff class inside the model you want to track, much like the normal Meta class:

```
class Pizza(SaveGeomodeldiffMixin, models.Model):
    # field definitions
    # Meta class

    # Modeldiff class
    class Modeldiff:
        model_name = 'my_module.Pizza'
        fields = ('name', 'ingredients',
                  'topping')
        geom_field = 'latlon'
        geom_precision = 8
````

Test
-----

For sqlite run "python quicktest.py modeldiff"

For postgres run "python quicktest.py modeldiff --db postgres"