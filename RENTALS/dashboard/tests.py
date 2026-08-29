from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from maintenance.models import Maintenance
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from units.models import Unit
from arrears.models import Arrears
from invoices.models import Invoice
from water_bills.models import WaterBill


class DashboardViewTests(TestCase):
    def test_dashboard_loads_for_logged_in_user(self):
        user = User.objects.create_user(username='dashboard-user', password='pass12345')
        self.client.login(username='dashboard-user', password='pass12345')

        response = self.client.get(reverse('dashboard_home'))

        self.assertEqual(response.status_code, 200)
        self.assertIn('total_revenue', response.context)
        self.assertIn('total_maintenance', response.context)
        self.assertIn('total_arrears', response.context)


class DashboardBreakdownTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='dashboard-owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Sunset Apartments',
            address='1st Street',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        self.tenant = Tenant.objects.create(
            unit=self.unit,
            first_name='John',
            last_name='Doe',
            phone_number='0700000000',
            next_of_kin_phone_number='0711111111',
        )

    def _today(self):
        return timezone.now().date()

    def _current_month_start(self):
        return self._today().replace(day=1)

    def _prev_month_start(self):
        return (self._current_month_start() - timedelta(days=1)).replace(day=1)

    def _date_in_current_month(self, day):
        start = self._current_month_start()
        year = start.year
        month = start.month
        last_day = monthrange(year, month)[1]
        return date(year, month, min(day, last_day))

    def _date_in_prev_month(self, day):
        start = self._prev_month_start()
        year = start.year
        month = start.month
        last_day = monthrange(year, month)[1]
        return date(year, month, min(day, last_day))

    def test_revenue_breakdown_includes_accessible_properties(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        tenant2 = Tenant.objects.create(
            unit=unit2,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
        )

        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            date=self._date_in_current_month(10),
            description='Current month prop1',
        )
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('3000.00'),
            date=self._date_in_prev_month(10),
            description='Prev month prop1',
        )
        Payment.objects.create(
            user=self.user,
            property=prop2,
            unit=unit2,
            tenant=tenant2,
            amount=Decimal('7000.00'),
            date=self._date_in_current_month(15),
            description='Current month prop2',
        )
        Payment.objects.create(
            user=self.user,
            property=prop2,
            unit=unit2,
            tenant=tenant2,
            amount=Decimal('4000.00'),
            date=self._date_in_prev_month(15),
            description='Prev month prop2',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['revenue_breakdown']
        self.assertEqual(len(breakdown), 2)

        prop1_data = next(b for b in breakdown if b['name'] == 'Sunset Apartments')
        self.assertEqual(prop1_data['amount'], Decimal('5000.00'))
        self.assertAlmostEqual(prop1_data['percentage'], 66.7, places=1)

        prop2_data = next(b for b in breakdown if b['name'] == 'Green Court')
        self.assertEqual(prop2_data['amount'], Decimal('7000.00'))
        self.assertAlmostEqual(prop2_data['percentage'], 75.0, places=1)

    def test_revenue_percentage_none_when_previous_month_zero(self):
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            date=self._date_in_current_month(10),
            description='Current only',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['revenue_breakdown']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['amount'], Decimal('5000.00'))
        self.assertIsNone(breakdown[0]['percentage'])

    def test_maintenance_breakdown_includes_accessible_properties(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )

        Maintenance.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            amount=Decimal('2000.00'),
            date=self._date_in_current_month(10),
            description='Current month prop1',
        )
        Maintenance.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            amount=Decimal('1000.00'),
            date=self._date_in_prev_month(10),
            description='Prev month prop1',
        )
        Maintenance.objects.create(
            user=self.user,
            property=prop2,
            unit=unit2,
            amount=Decimal('3000.00'),
            date=self._date_in_current_month(15),
            description='Current month prop2',
        )
        Maintenance.objects.create(
            user=self.user,
            property=prop2,
            unit=unit2,
            amount=Decimal('1500.00'),
            date=self._date_in_prev_month(15),
            description='Prev month prop2',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['maintenance_breakdown']
        self.assertEqual(len(breakdown), 2)

        prop1_data = next(b for b in breakdown if b['name'] == 'Sunset Apartments')
        self.assertEqual(prop1_data['amount'], Decimal('2000.00'))
        self.assertAlmostEqual(prop1_data['percentage'], 100.0, places=1)

        prop2_data = next(b for b in breakdown if b['name'] == 'Green Court')
        self.assertEqual(prop2_data['amount'], Decimal('3000.00'))
        self.assertAlmostEqual(prop2_data['percentage'], 100.0, places=1)

    def test_maintenance_percentage_none_when_previous_month_zero(self):
        Maintenance.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            amount=Decimal('2000.00'),
            date=self._date_in_current_month(10),
            description='Current only',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['maintenance_breakdown']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['amount'], Decimal('2000.00'))
        self.assertIsNone(breakdown[0]['percentage'])

    def test_breakdown_scoped_to_accessible_properties(self):
        other_user = User.objects.create_user(username='other-user', password='pass12345')
        other_prop = Property.objects.create(
            user=other_user,
            name='Other Property',
            address='Other Road',
            county='Mombasa',
            total_units=1,
            description='Other property',
        )
        other_unit = Unit.objects.create(
            user=other_user,
            property=other_prop,
            name='C1',
            rent_amount=Decimal('8000.00'),
            status='occupied',
        )
        other_tenant = Tenant.objects.create(
            unit=other_unit,
            first_name='Other',
            last_name='Tenant',
            phone_number='0700000002',
            next_of_kin_phone_number='0711111113',
        )

        Payment.objects.create(
            user=other_user,
            property=other_prop,
            unit=other_unit,
            tenant=other_tenant,
            amount=Decimal('6000.00'),
            date=self._date_in_current_month(5),
            description='Other user payment',
        )
        Maintenance.objects.create(
            user=other_user,
            property=other_prop,
            unit=other_unit,
            amount=Decimal('1500.00'),
            date=self._date_in_current_month(5),
            description='Other user maintenance',
        )

        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('4000.00'),
            date=self._date_in_current_month(10),
            description='My payment',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        revenue_names = [b['name'] for b in response.context['revenue_breakdown']]
        maint_names = [b['name'] for b in response.context['maintenance_breakdown']]
        self.assertNotIn('Other Property', revenue_names)
        self.assertNotIn('Other Property', maint_names)
        self.assertIn('Sunset Apartments', revenue_names)

    def test_breakdown_includes_property_with_zero_current_revenue(self):
        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('3000.00'),
            date=self._date_in_prev_month(10),
            description='Prev month only',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['revenue_breakdown']
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]['amount'], Decimal('0.00'))
        self.assertAlmostEqual(breakdown[0]['percentage'], -100.0, places=1)

    def test_dashboard_totals_match_breakdown_sums(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        tenant2 = Tenant.objects.create(
            unit=unit2,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
        )

        Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            date=self._date_in_current_month(5),
            description='Prop 1 payment',
            status='claimed',
        )
        Payment.objects.create(
            user=self.user,
            property=prop2,
            unit=unit2,
            tenant=tenant2,
            amount=Decimal('3000.00'),
            date=self._date_in_current_month(6),
            description='Prop 2 payment',
            status='claimed',
        )

        Maintenance.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            amount=Decimal('2000.00'),
            date=self._date_in_current_month(5),
            description='Prop 1 maint',
            status='pending',
        )

        invoice1 = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status='Unpaid',
        )
        invoice2 = Invoice.objects.create(
            user=self.user,
            unit=unit2,
            tenant=tenant2,
            amount=Decimal('3000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=5),
            status='Unpaid',
        )
        Arrears.objects.create(
            user=self.user,
            invoice=invoice1,
            tenant=self.tenant,
            unit=self.unit,
            amount_due=Decimal('5000.00'),
            days_overdue=10,
            status='pending',
        )
        Arrears.objects.create(
            user=self.user,
            invoice=invoice2,
            tenant=tenant2,
            unit=unit2,
            amount_due=Decimal('3000.00'),
            days_overdue=5,
            status='pending',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.context['total_revenue'], Decimal('8000.00'))
        self.assertEqual(response.context['total_maintenance'], Decimal('2000.00'))
        self.assertEqual(response.context['total_arrears'], Decimal('8000.00'))

        rev_sum = sum(item['amount'] for item in response.context['revenue_breakdown'])
        maint_sum = sum(item['amount'] for item in response.context['maintenance_breakdown'])
        arr_sum = sum(item['amount'] for item in response.context['arrears_breakdown'])
        self.assertEqual(rev_sum, Decimal('8000.00'))
        self.assertEqual(maint_sum, Decimal('2000.00'))
        self.assertEqual(arr_sum, Decimal('8000.00'))

    def test_property_breakdown_includes_all_accessible_properties(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=3,
            description='Second property',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['property_breakdown']
        self.assertEqual(len(breakdown), 2)
        names = [b['name'] for b in breakdown]
        self.assertIn('Sunset Apartments', names)
        self.assertIn('Green Court', names)

    def test_tenant_stats_includes_all_accessible_properties(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        Tenant.objects.create(
            unit=unit2,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        stats = response.context['tenant_stats']
        self.assertEqual(len(stats), 2)
        names = [s['name'] for s in stats]
        self.assertIn('Sunset Apartments', names)
        self.assertIn('Green Court', names)

    def test_maintenance_breakdown_includes_zero_maintenance_properties(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )

        Maintenance.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            amount=Decimal('2000.00'),
            date=self._date_in_current_month(10),
            description='Current month prop1',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['maintenance_breakdown']
        self.assertEqual(len(breakdown), 2)

        prop1_data = next(b for b in breakdown if b['name'] == 'Sunset Apartments')
        self.assertEqual(prop1_data['amount'], Decimal('2000.00'))

        prop2_data = next(b for b in breakdown if b['name'] == 'Green Court')
        self.assertEqual(prop2_data['amount'], Decimal('0.00'))

    def test_arrears_breakdown_includes_pending_arrears(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        tenant2 = Tenant.objects.create(
            unit=unit2,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
        )

        invoice1 = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal('5000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status='Unpaid',
        )
        invoice2 = Invoice.objects.create(
            user=self.user,
            unit=unit2,
            tenant=tenant2,
            amount=Decimal('3000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=5),
            status='Unpaid',
        )

        Arrears.objects.create(
            user=self.user,
            invoice=invoice1,
            tenant=self.tenant,
            unit=self.unit,
            amount_due=Decimal('5000.00'),
            days_overdue=10,
            status='pending',
        )
        Arrears.objects.create(
            user=self.user,
            invoice=invoice2,
            tenant=tenant2,
            unit=unit2,
            amount_due=Decimal('3000.00'),
            days_overdue=5,
            status='pending',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['arrears_breakdown']
        self.assertEqual(len(breakdown), 2)

        prop1_data = next(b for b in breakdown if b['name'] == 'Sunset Apartments')
        self.assertEqual(prop1_data['amount'], Decimal('5000.00'))

        prop2_data = next(b for b in breakdown if b['name'] == 'Green Court')
        self.assertEqual(prop2_data['amount'], Decimal('3000.00'))

    def test_arrears_breakdown_scoped_to_accessible_properties(self):
        other_user = User.objects.create_user(username='other-user', password='pass12345')
        other_prop = Property.objects.create(
            user=other_user,
            name='Other Property',
            address='Other Road',
            county='Mombasa',
            total_units=1,
            description='Other property',
        )
        other_unit = Unit.objects.create(
            user=other_user,
            property=other_prop,
            name='C1',
            rent_amount=Decimal('8000.00'),
            status='occupied',
        )
        other_tenant = Tenant.objects.create(
            unit=other_unit,
            first_name='Other',
            last_name='Tenant',
            phone_number='0700000002',
            next_of_kin_phone_number='0711111113',
        )

        other_invoice = Invoice.objects.create(
            user=other_user,
            unit=other_unit,
            tenant=other_tenant,
            amount=Decimal('6000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status='Unpaid',
        )
        Arrears.objects.create(
            user=other_user,
            invoice=other_invoice,
            tenant=other_tenant,
            unit=other_unit,
            amount_due=Decimal('6000.00'),
            days_overdue=10,
            status='pending',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['arrears_breakdown']
        names = [b['name'] for b in breakdown]
        self.assertNotIn('Other Property', names)
        self.assertIn('Sunset Apartments', names)

    def test_water_bills_breakdown_includes_current_month(self):
        prop2 = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='Main Road',
            county='Nairobi',
            total_units=1,
            description='Second property',
        )
        unit2 = Unit.objects.create(
            user=self.user,
            property=prop2,
            name='B1',
            rent_amount=Decimal('10000.00'),
            status='occupied',
        )
        tenant2 = Tenant.objects.create(
            unit=unit2,
            first_name='Jane',
            last_name='Doe',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
        )

        WaterBill.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            previous_reading=100,
            current_reading=150,
            rate=Decimal('50.00'),
            due_date=self._date_in_current_month(15),
            status='Unpaid',
        )
        WaterBill.objects.create(
            user=self.user,
            unit=unit2,
            tenant=tenant2,
            previous_reading=200,
            current_reading=250,
            rate=Decimal('40.00'),
            due_date=self._date_in_current_month(16),
            status='Unpaid',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['water_bills_breakdown']
        self.assertEqual(len(breakdown), 2)

        prop1_data = next(b for b in breakdown if b['name'] == 'Sunset Apartments')
        self.assertEqual(prop1_data['amount'], Decimal('2500.00'))

        prop2_data = next(b for b in breakdown if b['name'] == 'Green Court')
        self.assertEqual(prop2_data['amount'], Decimal('2000.00'))

        self.assertEqual(response.context['total_water_bills'], Decimal('4500.00'))

    def test_water_bills_breakdown_excludes_other_users(self):
        other_user = User.objects.create_user(username='other-user', password='pass12345')
        other_prop = Property.objects.create(
            user=other_user,
            name='Other Property',
            address='Other Road',
            county='Mombasa',
            total_units=1,
            description='Other property',
        )
        other_unit = Unit.objects.create(
            user=other_user,
            property=other_prop,
            name='C1',
            rent_amount=Decimal('8000.00'),
            status='occupied',
        )
        other_tenant = Tenant.objects.create(
            unit=other_unit,
            first_name='Other',
            last_name='Tenant',
            phone_number='0700000002',
            next_of_kin_phone_number='0711111113',
        )

        WaterBill.objects.create(
            user=other_user,
            unit=other_unit,
            tenant=other_tenant,
            previous_reading=100,
            current_reading=150,
            rate=Decimal('50.00'),
            due_date=self._date_in_current_month(15),
            status='Unpaid',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)
        breakdown = response.context['water_bills_breakdown']
        names = [b['name'] for b in breakdown]
        self.assertNotIn('Other Property', names)
        self.assertIn('Sunset Apartments', names)

    def test_all_breakdowns_sorted_alphabetically(self):
        Property.objects.create(
            user=self.user,
            name='Alpha Apartments',
            address='Alpha Road',
            county='Nairobi',
            total_units=1,
            description='Alpha property',
        )
        Property.objects.create(
            user=self.user,
            name='Zebra Complex',
            address='Zebra Road',
            county='Nairobi',
            total_units=1,
            description='Zebra property',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)

        tenant_names = [s['name'] for s in response.context['tenant_stats']]
        self.assertEqual(tenant_names, sorted(tenant_names))

        revenue_names = [b['name'] for b in response.context['revenue_breakdown']]
        self.assertEqual(revenue_names, sorted(revenue_names))

        maint_names = [b['name'] for b in response.context['maintenance_breakdown']]
        self.assertEqual(maint_names, sorted(maint_names))

        property_names = [b['name'] for b in response.context['property_breakdown']]
        self.assertEqual(property_names, sorted(property_names))

        arrears_names = [b['name'] for b in response.context['arrears_breakdown']]
        self.assertEqual(arrears_names, sorted(arrears_names))

        water_names = [b['name'] for b in response.context['water_bills_breakdown']]
        self.assertEqual(water_names, sorted(water_names))

    def test_duplicate_property_names_do_not_conflate_counts(self):
        prop_a = Property.objects.create(
            user=self.user,
            name='Twin Towers',
            address='1st Street',
            county='Nairobi',
            total_units=2,
            description='Twin A',
        )
        unit_a = Unit.objects.create(
            user=self.user,
            property=prop_a,
            name='A1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        tenant_a = Tenant.objects.create(
            unit=unit_a,
            first_name='Alice',
            last_name='Alpha',
            phone_number='0700000001',
            next_of_kin_phone_number='0711111112',
            status='active',
        )

        prop_b = Property.objects.create(
            user=self.user,
            name='Twin Towers',
            address='2nd Street',
            county='Nairobi',
            total_units=1,
            description='Twin B',
        )
        unit_b = Unit.objects.create(
            user=self.user,
            property=prop_b,
            name='B1',
            rent_amount=Decimal('8000.00'),
            status='occupied',
        )
        tenant_b = Tenant.objects.create(
            unit=unit_b,
            first_name='Bob',
            last_name='Beta',
            phone_number='0700000002',
            next_of_kin_phone_number='0711111113',
            status='inactive',
        )

        Payment.objects.create(
            user=self.user,
            property=prop_a,
            unit=unit_a,
            tenant=tenant_a,
            amount=Decimal('5000.00'),
            date=self._date_in_current_month(5),
            description='Prop A payment',
            status='claimed',
        )
        Payment.objects.create(
            user=self.user,
            property=prop_b,
            unit=unit_b,
            tenant=tenant_b,
            amount=Decimal('3000.00'),
            date=self._date_in_current_month(6),
            description='Prop B payment',
            status='claimed',
        )

        Maintenance.objects.create(
            user=self.user,
            property=prop_a,
            unit=unit_a,
            amount=Decimal('2000.00'),
            date=self._date_in_current_month(5),
            description='Prop A maint',
            status='pending',
        )
        Maintenance.objects.create(
            user=self.user,
            property=prop_b,
            unit=unit_b,
            amount=Decimal('1000.00'),
            date=self._date_in_current_month(6),
            description='Prop B maint',
            status='pending',
        )

        invoice_a = Invoice.objects.create(
            user=self.user,
            unit=unit_a,
            tenant=tenant_a,
            amount=Decimal('5000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=10),
            status='Unpaid',
        )
        invoice_b = Invoice.objects.create(
            user=self.user,
            unit=unit_b,
            tenant=tenant_b,
            amount=Decimal('3000.00'),
            type='Rent',
            due_date=timezone.now().date() - timedelta(days=5),
            status='Unpaid',
        )
        Arrears.objects.create(
            user=self.user,
            invoice=invoice_a,
            tenant=tenant_a,
            unit=unit_a,
            amount_due=Decimal('5000.00'),
            days_overdue=10,
            status='pending',
        )
        Arrears.objects.create(
            user=self.user,
            invoice=invoice_b,
            tenant=tenant_b,
            unit=unit_b,
            amount_due=Decimal('3000.00'),
            days_overdue=5,
            status='pending',
        )

        response = self.client.get(reverse('dashboard_home'))
        self.assertEqual(response.status_code, 200)

        # There should be 2 entries named 'Twin Towers' in breakdowns
        revenue = response.context['revenue_breakdown']
        twin_revenue = [r for r in revenue if r['name'] == 'Twin Towers']
        self.assertEqual(len(twin_revenue), 2)
        twin_revenue.sort(key=lambda r: r['amount'])
        self.assertEqual(twin_revenue[0]['amount'], Decimal('3000.00'))
        self.assertEqual(twin_revenue[1]['amount'], Decimal('5000.00'))

        maintenance = response.context['maintenance_breakdown']
        twin_maint = [r for r in maintenance if r['name'] == 'Twin Towers']
        self.assertEqual(len(twin_maint), 2)
        twin_maint.sort(key=lambda r: r['amount'])
        self.assertEqual(twin_maint[0]['amount'], Decimal('1000.00'))
        self.assertEqual(twin_maint[1]['amount'], Decimal('2000.00'))

        arrears = response.context['arrears_breakdown']
        twin_arrears = [r for r in arrears if r['name'] == 'Twin Towers']
        self.assertEqual(len(twin_arrears), 2)
        twin_arrears.sort(key=lambda r: r['amount'])
        self.assertEqual(twin_arrears[0]['amount'], Decimal('3000.00'))
        self.assertEqual(twin_arrears[1]['amount'], Decimal('5000.00'))

        tenant_stats = response.context['tenant_stats']
        twin_stats = [s for s in tenant_stats if s['name'] == 'Twin Towers']
        self.assertEqual(len(twin_stats), 2)
        twin_stats.sort(key=lambda s: (s['active'], s['inactive']))
        self.assertEqual(twin_stats[0]['active'], 0)
        self.assertEqual(twin_stats[0]['inactive'], 1)
        self.assertEqual(twin_stats[1]['active'], 1)
        self.assertEqual(twin_stats[1]['inactive'], 0)
