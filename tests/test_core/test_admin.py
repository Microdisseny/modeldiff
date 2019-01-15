from django.test import TestCase
from django.urls import reverse

from helpers import create_superuser


class ModeldiffAdminTests(TestCase):

    def setUp(self):
        self.superuser = create_superuser()
        self.client.login(username='admin', password='admin')

    def test_modeldiff_app_index_get(self):
        url = reverse('admin:app_list', args=('modeldiff',))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_modeldiff_modeldiff_changelist(self):
        url = reverse('admin:modeldiff_modeldiff_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_modeldiff_modeldiff_changelist_filtered(self):
        url = reverse('admin:modeldiff_modeldiff_changelist')
        response = self.client.get(url, {'model_name': 'core.PersonModel'})
        self.assertEqual(response.status_code, 200)

    def test_modeldiff_geomodeldiff_changelist(self):
        url = reverse('admin:modeldiff_geomodeldiff_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
