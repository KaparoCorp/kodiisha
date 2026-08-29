from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from leases.models import Lease


class UnitsViewTests(TestCase):
    def test_units_page_loads_for_logged_in_user(self):
        user = User.objects.create_user(username='units-user', password='pass12345')
        self.client.login(username='units-user', password='pass12345')

        response = self.client.get(reverse('units:units_list'))

        self.assertEqual(response.status_code, 200)


class UploadUnitsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='pass12345')
        self.client.login(username='owner', password='pass12345')
        self.property = Property.objects.create(
            user=self.user,
            name='RANASA 1',
            address='Nairobi',
            county='Nairobi',
            total_units=0,
            description='Test property',
        )

    def upload(self, content, filename='units.csv'):
        uploaded_file = SimpleUploadedFile(
            filename,
            content.encode('utf-8'),
            content_type='text/csv',
        )
        return self.client.post(reverse('units:upload_units'), {'file': uploaded_file})

    def test_upload_accepts_tab_separated_unit_file(self):
        response = self.upload(
            "property\tname\trent_amount\tdescription\tstatus\n"
            "RANASA 1\tShop 1\t15,000\tShop 1\t\n"
            "RANASA 1\tHouse G1\t7,500\tGround floor\t\n"
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['errors'], [])
        self.assertEqual(Unit.objects.count(), 2)
        self.assertEqual(Unit.objects.get(name='Shop 1').rent_amount, Decimal('15000.00'))
        self.assertEqual(Unit.objects.get(name='Shop 1').status, 'vacant')

    def test_upload_repairs_unquoted_comma_in_rent_amount(self):
        response = self.upload(
            "property,name,rent_amount,description,status\n"
            "RANASA 1,Shop 1,15,000,Shop 1,\n"
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        unit = Unit.objects.get(name='Shop 1')
        self.assertEqual(unit.rent_amount, Decimal('15000.00'))
        self.assertEqual(unit.description, 'Shop 1')
        self.assertEqual(unit.status, 'vacant')

    def test_upload_returns_row_numbered_errors_in_response(self):
        response = self.upload(
            "property\tname\trent_amount\tdescription\tstatus\n"
            "RANASA 1\tShop 1\t15,000\tShop 1\t\n"
            "MISSING\tShop 2\tbad\tShop 2\t\n"
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['invalid_rows'], 1)
        self.assertIn('Row 3: Property "MISSING" not found for this user', data['errors'])

    def test_validate_only_does_not_create_units(self):
        uploaded_file = SimpleUploadedFile(
            'units.csv',
            b'property,name,rent_amount,description,status\nRANASA 1,Shop 1,15,000,Shop 1,\n',
            content_type='text/csv',
        )

        response = self.client.post(
            reverse('units:upload_units'),
            {'file': uploaded_file, 'validate_only': '1'},
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(Unit.objects.count(), 0)

    def test_units_list_filters_by_status_and_preserves_selected_option(self):
        occupied_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='Occupied 1',
            rent_amount=Decimal('12000.00'),
            status='occupied',
        )
        Unit.objects.create(
            user=self.user,
            property=self.property,
            name='Vacant 1',
            rent_amount=Decimal('9000.00'),
            status='vacant',
        )

        response = self.client.get(reverse('units:units_list'), {'status': 'occupied'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, occupied_unit.name)
        self.assertNotContains(response, 'Vacant 1')
        self.assertContains(response, '<option value="occupied" selected>Occupied</option>', html=True)


class AddUnitTenantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='owner2', password='pass12345')
        self.client.login(username='owner2', password='pass12345')
        self.property = Property.objects.create(
            user=self.user,
            name='BLOCK A',
            address='Nairobi',
            county='Nairobi',
            total_units=0,
            description='Test property',
        )
        # An available (inactive, unassigned) tenant.
        self.tenant = Tenant.objects.create(
            unit=None,
            first_name='Jane',
            last_name='Doe',
            phone_number='0712000000',
            next_of_kin_phone_number='0712000001',
            status='inactive',
        )

    def _post_unit(self, tenant_id=''):
        data = {
            'property': self.property.pk,
            'name': 'Unit X',
            'rent_amount': '10000.00',
            'status': 'occupied',
            'tenant': tenant_id,
        }
        return self.client.post(reverse('units:units_list'), data, follow=True)

    def test_unit_can_be_created_without_a_tenant(self):
        response = self._post_unit(tenant_id='')
        self.assertEqual(response.status_code, 200)

        unit = Unit.objects.get(name='Unit X')
        self.assertIsNone(unit.leases.filter(is_active=True).first())
        # No tenant should have been auto-attached.
        self.tenant.refresh_from_db()
        self.assertIsNone(self.tenant.unit)

    def test_unit_gets_tenant_only_when_explicitly_selected(self):
        response = self._post_unit(tenant_id=str(self.tenant.pk))
        self.assertEqual(response.status_code, 200)

        unit = Unit.objects.get(name='Unit X')
        lease = unit.leases.filter(is_active=True).first()
        self.assertIsNotNone(lease)
        self.assertEqual(lease.tenant, self.tenant)
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.unit, unit)
        self.assertEqual(self.tenant.status, 'active')

