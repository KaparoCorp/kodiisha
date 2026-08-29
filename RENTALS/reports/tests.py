from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from invoices.models import Invoice
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit
from water_bills.models import WaterBill


class ReportFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )
        self.other_property = Property.objects.create(
            user=self.user,
            name='Blue Court',
            address='Side Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
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

    def make_water_bill(self, unit, tenant, due_date):
        return WaterBill.objects.create(
            user=self.user,
            unit=unit,
            tenant=tenant,
            previous_reading=10,
            current_reading=20,
            rate=Decimal('10.00'),
            due_date=due_date,
        )

    def test_report_filters_totals_by_property_and_single_start_date(self):
        included_invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('12000.00'),
            type='Rent',
            due_date=date(2026, 5, 15),
        )
        Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('11000.00'),
            type='Rent',
            due_date=date(2026, 4, 15),
        )
        Invoice.objects.create(
            user=self.user,
            unit=self.other_unit,
            tenant=self.other_tenant,
            amount=Decimal('9000.00'),
            type='Rent',
            due_date=date(2026, 5, 15),
        )
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('8000.00'),
            date=date(2026, 5, 16),
        )
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('7000.00'),
            date=date(2026, 4, 16),
        )
        self.make_water_bill(self.unit, self.tenant, date(2026, 5, 17))
        self.make_water_bill(self.unit, self.tenant, date(2026, 4, 17))
        self.make_water_bill(self.other_unit, self.other_tenant, date(2026, 5, 17))

        response = self.client.get(reverse('reports:report_generator'), {
            'property': self.property.id,
            'start_date': '2026-05-01',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['rent_expected'], Decimal('12000.00'))
        self.assertEqual(response.context['rent_collected'], Decimal('8000.00'))
        self.assertEqual(response.context['water_total'], Decimal('100.00'))
        self.assertEqual(list(response.context['recent_invoices']), [included_invoice])
