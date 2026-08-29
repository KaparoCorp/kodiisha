from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from properties.models import Property
from units.models import Unit


class LeaseFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='lease-owner', password='pass12345')
        self.client.force_login(self.user)
        self.property_one = Property.objects.create(
            user=self.user,
            name='Ranasa 1',
            address='1 Main Road',
            county='Nairobi',
            total_units=1,
            description='First property',
        )
        self.property_two = Property.objects.create(
            user=self.user,
            name='Ranasa 2',
            address='2 Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        self.unit_one = Unit.objects.create(
            user=self.user,
            property=self.property_one,
            name='A1',
            rent_amount='5000.00',
            description='First unit',
        )
        self.unit_two = Unit.objects.create(
            user=self.user,
            property=self.property_two,
            name='B1',
            rent_amount='6000.00',
            description='Second unit',
        )

    def test_lease_page_unit_filter_matches_selected_property(self):
        response = self.client.get(reverse('leases_home'), {'property': self.property_one.id})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A1 (Ranasa 1)')
        self.assertNotContains(response, 'B1 (Ranasa 2)')

    def test_units_endpoint_returns_units_for_selected_property_only(self):
        response = self.client.get(reverse('lease_units_for_property'), {'property': self.property_one.id})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['units'],
            [{'id': self.unit_one.id, 'name': 'A1', 'property': 'Ranasa 1'}],
        )
