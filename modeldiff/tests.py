from django.test import TestCase
from django.contrib.gis.utils.wkt import precision_wkt

import json

from test_models import PersonModel
from models import Geomodeldiff


class ModeldiffTests(TestCase):

    def setUp(self):
        PersonModel.objects.create(name='Foo', surname='Doe',
                                   the_geom='POINT (0 0)')
        diff = Geomodeldiff.objects.all()[0]

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
        print >> sys.stderr, '  the_geom:', diff.the_geom
        print >> sys.stderr, '  ---------'

    def test_creation_diff_exists(self):
        diff = Geomodeldiff.objects.all()[0]
        self.assertEqual(diff.id, 1)
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(diff.model_name, 'modeldiff.PersonModel')
        self.assertEqual(diff.old_data, '')
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Foo', 'surname': 'Doe'})
        self.assertEqual(precision_wkt(diff.the_geom, 8),
                         'POINT(0.00000000 0.00000000)')

    def test_modify_model(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.name = 'Bar'
        person.save()
        person.name = 'John'
        person.save()

        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'Bar'})

        diff = Geomodeldiff.objects.get(pk=3)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {'name': 'Bar', 'surname': 'Doe',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'John'})

    def test_delete_model(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.delete()

        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(diff.new_data, '')

    def test_set_to_none(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.surname = None
        person.the_geom = None
        person.save()

        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data),
                         {u'surname': None, u'the_geom': None})
