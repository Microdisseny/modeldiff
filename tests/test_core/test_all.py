from django.test import TestCase
from django.contrib.gis.utils.wkt import precision_wkt
from datetime import date, datetime, tzinfo, timedelta

import json

from core.models import PersonModel, PersonGeoModel
from core.models import PersonPropertyModel, PersonPropertyForGeoModel
from modeldiff.models import Geomodeldiff, Modeldiff


class GMT0(tzinfo):
    """
    tzinfo subclass that represents the timezone in Greenwich,
    or Greenwich Mean Time (GMT+0).
    This is used internally.
    """
    def utcoffset(self, dt):
        return timedelta(hours=0)

    def tzname(self, dt):
        return "GMT+0"

    def dst(self, dt):
        return timedelta(0)


class ModeldiffTests(TestCase):

    def setUp(self):
        self.person = PersonModel.objects.create(
            name='Foo', surname='Doe', birthdate=date(2007, 12, 5),
            updated_at=datetime(2015, 1, 7, 22, 0, 10, 292032, GMT0()))

        self.persongeo = PersonGeoModel.objects.create(
            name='Foo', surname='Doe', birthdate=date(2007, 12, 5),
            updated_at=datetime(2015, 1, 7, 22, 0, 10, 292032, GMT0()),
            the_geom='POINT (0 0)')

    def print_diff(self, diff):
        import sys
        print >> sys.stderr, '  ---------'
        print >> sys.stderr, '  id:', diff.id
        print >> sys.stderr, '  date_created:', diff.date_created
        print >> sys.stderr, '  action:', diff.action
        print >> sys.stderr, '  model_id:', diff.model_id
        print >> sys.stderr, '  model_name:', diff.model_name
        print >> sys.stderr, '  old_data:', diff.old_data
        print >> sys.stderr, '  new_data:', diff.new_data
        if hasattr(diff, 'the_geom'):
            print >> sys.stderr, '  the_geom:', diff.the_geom
        print >> sys.stderr, '  ---------'

    def test_creation_diff_exists(self):
        diff = Modeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.id, 1)
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_id, self.person.id)
        self.assertEqual(diff.model_name, 'modeldiff.PersonModel')
        self.assertEqual(diff.old_data, '')

        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Foo', 'surname': 'Doe',
                          'birthdate': '2007-12-05',
                          'updated_at': '2015-01-07 22:00:10.292032+0000'
                          })

    def test_modify_model(self):

        self.person.name = 'Bar'
        self.person.birthdate = date(2010, 10, 1)
        self.person.updated_at = datetime(2015, 1, 7, 23, 12, 11, 292032,
                                          GMT0())
        self.person.save()

        diff = Modeldiff.objects.all().order_by('-id')[:1][0]

        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.person.id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Bar',
                          'birthdate': '2010-10-01',
                          'updated_at': '2015-01-07 23:12:11.292032+0000',
                          })

        self.person.name = 'John'
        self.person.birthdate = date(2008, 11, 2)
        self.person.updated_at = datetime(2015, 1, 7, 23, 39, 13, 292032,
                                          GMT0())
        self.person.save()

        diff = Modeldiff.objects.all().order_by('-id')[:1][0]

        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.person.id)
        self.assertEqual(json.loads(diff.old_data),
                         {'name': 'Bar', 'surname': 'Doe',
                          u'birthdate': '2010-10-01',
                          u'updated_at': '2015-01-07 23:12:11.292032+0000'})
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'John',
                          'birthdate': '2008-11-02',
                          'updated_at': '2015-01-07 23:39:13.292032+0000',
                          })

    def test_delete_model(self):

        person_id = self.person.id
        self.person.delete()

        diff = Modeldiff.objects.all().last()
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_id, person_id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(diff.new_data, '')

    def test_set_to_none(self):
        self.person.surname = None
        self.person.save()

        diff = Modeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.person.id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': u'2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(json.loads(diff.new_data),
                         {u'surname': None})

    def test_update_parent_field_model(self):
        person_property = PersonPropertyModel.objects.create(
            person=self.person, address="Carme 15, Girona")

        diffs = Modeldiff.objects.all().order_by('-id')[:2]

        self.assertEqual(diffs[0].action, 'update')
        self.assertEqual(diffs[0].model_name, 'modeldiff.PersonModel')
        self.assertEqual(diffs[0].model_id, person_property.person.id)

        self.assertEqual(diffs[1].action, 'add')
        self.assertEqual(diffs[1].model_name, 'modeldiff.PersonPropertyModel')
        self.assertEqual(diffs[1].model_id, person_property.id)

    def test_delete_parent_field_model(self):
        person_property = PersonPropertyModel.objects.create(
            person=self.person, address="Carme 15, Girona")
        person_property_id = person_property.id
        person_property.delete()

        diffs = Modeldiff.objects.all().order_by('-id')[:2]

        self.assertEqual(diffs[0].action, 'update')
        self.assertEqual(diffs[0].model_name, 'modeldiff.PersonModel')
        self.assertEqual(diffs[0].model_id, self.person.id)

        self.assertEqual(diffs[1].action, 'delete')
        self.assertEqual(diffs[1].model_name, u'modeldiff.PersonPropertyModel')
        self.assertEqual(diffs[1].model_id, person_property_id)

    # Geo tests
    def test_geo_creation_diff_exists(self):

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]

        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_id, self.persongeo.id)
        self.assertEqual(diff.model_name, 'modeldiff.PersonGeoModel')
        self.assertEqual(diff.old_data, '')

        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Foo', 'surname': 'Doe',
                          'birthdate': '2007-12-05',
                          'updated_at': '2015-01-07 22:00:10.292032+0000',
                          'the_geom': 'POINT(0.00000000 0.00000000)'
                          })
        self.assertEqual(precision_wkt(diff.the_geom, 8),
                         'POINT(0.00000000 0.00000000)')

    def test_geo_modify_model(self):
        self.persongeo.name = 'Bar'
        self.persongeo.birthdate = date(2010, 10, 1)
        self.persongeo.updated_at = datetime(2015, 1, 7, 23, 12, 11, 292032,
                                             GMT0())
        self.persongeo.save()

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.persongeo.id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Bar',
                          'birthdate': '2010-10-01',
                          'updated_at': '2015-01-07 23:12:11.292032+0000',
                          })

        self.persongeo.name = 'John'
        self.persongeo.birthdate = date(2008, 11, 2)
        self.persongeo.updated_at = datetime(2015, 1, 7, 23, 39, 13, 292032,
                                             GMT0())
        self.persongeo.save()

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.persongeo.id)
        self.assertEqual(json.loads(diff.old_data),
                         {'name': 'Bar', 'surname': 'Doe',
                          u'birthdate': '2010-10-01',
                          u'updated_at': '2015-01-07 23:12:11.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'John',
                          'birthdate': '2008-11-02',
                          'updated_at': '2015-01-07 23:39:13.292032+0000',
                          })

    def test_geo_delete_model(self):

        persongeo_id = self.persongeo.id
        self.persongeo.delete()

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_id, persongeo_id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(diff.new_data, '')

    def test_geo_set_to_none(self):
        self.persongeo.surname = None
        self.persongeo.the_geom = None
        self.persongeo.save()

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, self.persongeo.id)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': u'2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data),
                         {u'surname': None, u'the_geom': None})

    def test_update_parent_field_geo_model(self):

        person_property = PersonPropertyForGeoModel.objects.create(
            person=self.persongeo, address="Carme 15, Girona")

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]

        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_name, 'modeldiff.PersonGeoModel')
        self.assertEqual(diff.model_id, person_property.person.id)

        self.assertEqual(diff.new_data, '{}')

        diff = Modeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_name,
                         'modeldiff.PersonPropertyForGeoModel')
        self.assertEqual(diff.model_id, person_property.id)

    def test_geo_delete_parent_field_model(self):
        person_property = PersonPropertyForGeoModel.objects.create(
            person=self.persongeo, address="Carme 15, Girona")

        person_property_id = person_property.id
        person_property.delete()

        diff = Geomodeldiff.objects.all().order_by('-id')[:1][0]

        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_name, 'modeldiff.PersonGeoModel')
        self.assertEqual(diff.model_id, self.persongeo.id)

        self.assertEqual(diff.new_data, '{}')

        diff = Modeldiff.objects.all().order_by('-id')[:1][0]
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_name,
                         'modeldiff.PersonPropertyForGeoModel')
        self.assertEqual(diff.model_id, person_property_id)
