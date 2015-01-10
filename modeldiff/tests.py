from django.test import TestCase
from django.contrib.gis.utils.wkt import precision_wkt
from datetime import date, datetime, tzinfo, timedelta

import json

from test_models import PersonModel, PersonGeoModel
from test_models import PersonPropertyModel, PersonPropertyForGeoModel
from models import Geomodeldiff, Modeldiff


class GMT0(tzinfo):
    """ tzinfo subclass that represents the timezone in Greenwich,
        or Greenwich Mean Time (GMT+0). 
        
        This is used internally.
    """
    def utcoffset(self, dt):
        return timedelta(hours=0)
    def tzname(self,dt): 
        return "GMT+0" 
    def dst(self,dt): 
        return timedelta(0)
    

class ModeldiffTests(TestCase):

    def setUp(self):
        PersonModel.objects.create(name='Foo', surname='Doe',
                                   birthdate=date(2007, 12, 5),
                                   updated_at=datetime(2015, 1, 7, 22, 0, 10, 
                                    292032, GMT0()))
        
        PersonGeoModel.objects.create(name='Foo', surname='Doe',
                                   birthdate=date(2007, 12, 5),
                                   updated_at=datetime(2015, 1, 7, 22, 0, 10, 
                                    292032, GMT0()),
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
        diff = Modeldiff.objects.all()[0]
        self.assertEqual(diff.id, 1)
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(diff.model_name, 'modeldiff.PersonModel')
        self.assertEqual(diff.old_data, '')
         
        self.assertEqual(json.loads(diff.new_data),
                         {'name': 'Foo', 'surname': 'Doe', 
                          'birthdate': '2007-12-05',
                          'updated_at': '2015-01-07 22:00:10.292032+0000'
                          })
 
    def test_modify_model(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.name = 'Bar'
        person.birthdate = date(2010, 10, 1)
        person.updated_at = datetime(2015, 1, 7, 23, 12, 11, 292032, GMT0())
        person.save()
         
        person.name = 'John'
        person.birthdate = date(2008, 11, 2)
        person.updated_at = datetime(2015, 1, 7, 23, 39, 13, 292032, GMT0())
        person.save()
  
        diff = Modeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'Bar', 
                            'birthdate': '2010-10-01',
                            'updated_at': '2015-01-07 23:12:11.292032+0000',                               
                            })
  
        diff = Modeldiff.objects.get(pk=3)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {'name': 'Bar', 'surname': 'Doe',
                          u'birthdate': '2010-10-01',
                          u'updated_at': '2015-01-07 23:12:11.292032+0000'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'John',
                            'birthdate': '2008-11-02',
                            'updated_at': '2015-01-07 23:39:13.292032+0000',                               
                            })
  
    def test_delete_model(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.delete()
   
        diff = Modeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(diff.new_data, '')
 
    def test_set_to_none(self):
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.surname = None
        person.save()
   
        diff = Modeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': u'2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000'})
        self.assertEqual(json.loads(diff.new_data),
                         {u'surname': None})
     
    def test_update_parent_field_model(self):
            
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
    
        person_property = PersonPropertyModel.objects.create(person=person, 
            address="Carme 15, Girona")
      
        diffs = Modeldiff.objects.all().order_by('-id')[:2]
           
        self.assertEqual(diffs[0].action, 'update')
        self.assertEqual(diffs[0].model_name, 'modeldiff.PersonModel')
        self.assertEqual(diffs[0].model_id, person_property.person.pk)
        
        self.assertEqual(diffs[1].action, 'add')
        self.assertEqual(diffs[1].model_name, 'modeldiff.PersonPropertyModel')
        self.assertEqual(diffs[1].model_id, person_property.pk)

    def test_delete_parent_field_model(self):
            
        person = PersonModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
    
        person_property = PersonPropertyModel.objects.create(person=person, 
            address="Carme 15, Girona")
        person_property_pk = person_property.person.pk
        person_property.delete()
      
        diffs = Modeldiff.objects.all().order_by('-id')[:2]
           
        self.assertEqual(diffs[0].action, 'update')
        self.assertEqual(diffs[0].model_name, 'modeldiff.PersonModel')
        self.assertEqual(diffs[0].model_id, person.pk)
        
        self.assertEqual(diffs[1].action, 'delete')
        self.assertEqual(diffs[1].model_name, u'modeldiff.PersonPropertyModel')
        self.assertEqual(diffs[1].model_id, person_property_pk)

            
    #Geo tests
    def test_geo_creation_diff_exists(self):
        diff = Geomodeldiff.objects.all()[0]
        self.assertEqual(diff.id, 1)
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_id, 1)
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
        person = PersonGeoModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.name = 'Bar'
        person.birthdate = date(2010, 10, 1)
        person.updated_at = datetime(2015, 1, 7, 23, 12, 11, 292032, GMT0())
        person.save()
          
        person.name = 'John'
        person.birthdate = date(2008, 11, 2)
        person.updated_at = datetime(2015, 1, 7, 23, 39, 13, 292032, GMT0())
        person.save()
   
        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'Bar', 
                            'birthdate': '2010-10-01',
                            'updated_at': '2015-01-07 23:12:11.292032+0000',                               
                            })
   
        diff = Geomodeldiff.objects.get(pk=3)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {'name': 'Bar', 'surname': 'Doe',
                          u'birthdate': '2010-10-01',
                          u'updated_at': '2015-01-07 23:12:11.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data), {'name': 'John',
                            'birthdate': '2008-11-02',
                            'updated_at': '2015-01-07 23:39:13.292032+0000',                               
                            })
   
    def test_geo_delete_model(self):
        person = PersonGeoModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.delete()
    
        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': '2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(diff.new_data, '')
  
    def test_geo_set_to_none(self):
        person = PersonGeoModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
        person.surname = None
        person.the_geom = None
        person.save()
    
        diff = Geomodeldiff.objects.get(pk=2)
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_id, 1)
        self.assertEqual(json.loads(diff.old_data),
                         {u'name': u'Foo', u'surname': u'Doe',
                          u'birthdate': u'2007-12-05',
                          u'updated_at': '2015-01-07 22:00:10.292032+0000',
                          u'the_geom': u'POINT(0.00000000 0.00000000)'})
        self.assertEqual(json.loads(diff.new_data),
                         {u'surname': None, u'the_geom': None})
     
    def test_update_parent_field_geo_model(self):
           
        person = PersonGeoModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
   
        person_property = PersonPropertyForGeoModel.objects.create(
            person=person, address="Carme 15, Girona")
     
        diff = Geomodeldiff.objects.latest('id')
          
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_name, 'modeldiff.PersonGeoModel')
        self.assertEqual(diff.model_id, person_property.person.pk)
       
        self.assertEqual(diff.new_data, '{}')
          
       
        diff = Modeldiff.objects.latest('id')
        self.assertEqual(diff.action, 'add')
        self.assertEqual(diff.model_name, 'modeldiff.PersonPropertyForGeoModel')
        self.assertEqual(diff.model_id, person_property.pk)

    def test_geo_delete_parent_field_model(self):
           
        person = PersonGeoModel.objects.get(pk=1)
        self.assertEqual(person.pk, 1)
   
        person_property = PersonPropertyForGeoModel.objects.create(
            person=person, address="Carme 15, Girona")
        
        person_property_pk = person_property.person.pk
        person_property.delete()
             
        diff = Geomodeldiff.objects.latest('id')
          
        self.assertEqual(diff.action, 'update')
        self.assertEqual(diff.model_name, 'modeldiff.PersonGeoModel')
        self.assertEqual(diff.model_id, person_property.person.pk)
       
        self.assertEqual(diff.new_data, '{}')
       
        diff = Modeldiff.objects.latest('id')
        self.assertEqual(diff.action, 'delete')
        self.assertEqual(diff.model_name, 'modeldiff.PersonPropertyForGeoModel')
        self.assertEqual(diff.model_id, person_property_pk) 
