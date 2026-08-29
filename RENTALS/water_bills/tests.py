from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from properties.models import Property
from tenants.models import Tenant
from units.models import Unit
from water_bills.models import WaterBill


class WaterBillFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=2,
            description='Test property',
        )
        self.other_property = Property.objects.create(
            user=self.user,
            name='Blue Court',
            address='Side Road',
            county='Nairobi',
            total_units=1,
            description='Other test property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        self.other_unit = Unit.objects.create(
            user=self.user,
            property=self.other_property,
            name='B1',
            rent_amount=Decimal('9000.00'),
            status='occupied',
        )
        self.tenant = Tenant.objects.create(
            unit=self.unit,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000000',
            next_of_kin_phone_number='0711111111',
        )
        self.other_tenant = Tenant.objects.create(
            unit=self.other_unit,
            first_name='John',
            last_name='Smith',
            phone_number='0722222222',
            next_of_kin_phone_number='0733333333',
        )

    def make_bill(self, unit, tenant, due_date, status='Unpaid'):
        return WaterBill.objects.create(
            user=self.user,
            unit=unit,
            tenant=tenant,
            previous_reading=10,
            current_reading=20,
            rate=Decimal('10.00'),
            due_date=due_date,
            status=status,
        )

    def test_water_bill_list_filters_by_property_unit_status_and_dates(self):
        selected_bill = self.make_bill(self.unit, self.tenant, date(2026, 5, 15), status='Paid')
        self.make_bill(self.unit, self.tenant, date(2026, 4, 15), status='Paid')
        self.make_bill(self.unit, self.tenant, date(2026, 5, 20), status='Unpaid')
        self.make_bill(self.other_unit, self.other_tenant, date(2026, 5, 15), status='Paid')

        response = self.client.get(reverse('water_bills:water_bills_home'), {
            'property': self.property.id,
            'unit': self.unit.id,
            'status': 'Paid',
            'start_date': '2026-05-01',
            'end_date': '2026-05-31',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context['bills']), [selected_bill])
        self.assertContains(response, '<option value="Paid" selected>Paid</option>', html=True)
        self.assertContains(response, 'value="2026-05-01"')
        self.assertContains(response, 'value="2026-05-31"')
