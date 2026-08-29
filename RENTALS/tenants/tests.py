import shutil
import tempfile
from datetime import date
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from invoices.models import Invoice
from leases.models import Lease
from payments.forms import PaymentForm
from payments.models import Payment
from properties.models import Property
from units.forms import UnitForm
from units.models import Unit

from .forms import TenantForm
from .models import Tenant


TEST_MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class TenantDocumentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='owner', password='password12345')
        self.property = Property.objects.create(
            user=self.user,
            name='Test Property',
            address='123 Test Street',
            county='Nairobi',
            total_units=1,
            description='Test property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='T1',
            rent_amount=Decimal('10000.00'),
            status='vacant',
        )

    def test_document_fields_are_optional(self):
        form = TenantForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
        }, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)

    def test_add_tenant_accepts_id_card_front_back_and_kra_pin_text(self):
        self.client.login(username='owner', password='password12345')

        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
        })

        self.assertEqual(response.status_code, 302)
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertEqual(tenant.first_name, 'Jane')
        self.assertEqual(tenant.last_name, 'Doe')

    def test_upload_tenants_accepts_basic_csv_headers(self):
        self.client.login(username='owner', password='password12345')
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property,next_of_kin_phone_number\n'
                'Jane,Doe,0712345678,Test Property,0798765432\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(reverse('tenants:upload_tenants'), {'file': csv_file})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertEqual(tenant.first_name, 'Jane')
        self.assertEqual(tenant.last_name, 'Doe')
        self.assertEqual(tenant.unit, self.unit)

    def test_validate_only_does_not_create_tenants(self):
        self.client.login(username='owner', password='password12345')
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property\n'
                'Jane,Doe,0712345678,Test Property\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(
            reverse('tenants:upload_tenants'),
            {'file': csv_file, 'validate_only': '1'},
        )

        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(Tenant.objects.count(), 0)

    def test_validate_only_with_errors_returns_failure(self):
        self.client.login(username='owner', password='password12345')
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property\n'
                'Jane,Doe,0712345678,Test Property\n'
                'John,Smith,0712345679,Nonexistent Property\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(
            reverse('tenants:upload_tenants'),
            {'file': csv_file, 'validate_only': '1'},
        )

        data = response.json()
        self.assertFalse(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(Tenant.objects.count(), 0)
        self.assertEqual(data['valid_rows'], 1)
        self.assertEqual(data['invalid_rows'], 1)

    def test_add_tenant_via_form_assigns_unit_and_appears_in_list(self):
        self.client.login(username='owner', password='password12345')

        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertIsNotNone(tenant.unit)
        self.assertEqual(tenant.unit, self.unit)
        self.assertEqual(tenant.unit.status, 'occupied')
        self.assertContains(response, 'Jane Doe')

    def test_kra_pin_valid_format(self):
        form = TenantForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
            'kra_pin': 'A123456789B',
        }, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['kra_pin'], 'A123456789B')

    def test_kra_pin_invalid_format(self):
        form = TenantForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
            'kra_pin': '12345',
        }, user=self.user)

        self.assertFalse(form.is_valid())
        self.assertIn('kra_pin', form.errors)

    def test_kra_pin_normalized_to_uppercase(self):
        form = TenantForm(data={
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
            'kra_pin': 'a123456789b',
        }, user=self.user)

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['kra_pin'], 'A123456789B')

    def test_id_photos_accepted(self):
        self.client.login(username='owner', password='password12345')
        try:
            from PIL import Image
            import io
            img = Image.new('RGB', (1, 1), color='red')
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            png_bytes = buf.getvalue()
        except ImportError:
            png_bytes = (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02'
                b'\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03'
                b'\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82'
            )
        front_file = SimpleUploadedFile('front.png', png_bytes, content_type='image/png')
        back_file = SimpleUploadedFile('back.png', png_bytes, content_type='image/png')

        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'status': 'active',
            'deposit_required': 'on',
            'deposit_amount': '0.00',
            'kra_pin': 'A123456789B',
            'id_card_front': front_file,
            'id_card_back': back_file,
        })

        self.assertEqual(response.status_code, 302)
        tenant = Tenant.objects.get(first_name='Jane')
        self.assertTrue(tenant.id_card_front)
        self.assertTrue(tenant.id_card_back)
        self.assertEqual(tenant.kra_pin, 'A123456789B')

    def test_upload_tenants_marks_unit_as_occupied(self):
        self.client.login(username='owner', password='password12345')
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property\n'
                'Jane,Doe,0712345678,Test Property\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(reverse('tenants:upload_tenants'), {'file': csv_file})

        data = response.json()
        self.assertTrue(data['success'])
        self.unit.refresh_from_db()
        self.assertEqual(self.unit.status, 'occupied')


class ScopedFormQuerysetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='scoped-form-owner', password='pass12345')
        self.own_property = Property.objects.create(
            user=self.user,
            name='Owned Property',
            address='1 Owned Road',
            county='Nairobi',
            total_units=1,
            description='Owned property',
        )
        self.own_unit = Unit.objects.create(
            user=self.user,
            property=self.own_property,
            name='B1',
            rent_amount='3000.00',
            description='Owned unit',
        )
        self.other_user = User.objects.create_user(username='other-form-owner', password='pass12345')
        self.other_property = Property.objects.create(
            user=self.other_user,
            name='Other Property',
            address='2 Other Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
        )
        self.other_unit = Unit.objects.create(
            user=self.other_user,
            property=self.other_property,
            name='C1',
            rent_amount='4000.00',
            description='Other unit',
        )

    def test_tenant_form_only_lists_owned_properties(self):
        form = TenantForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])

    def test_unit_form_only_lists_owned_properties(self):
        form = UnitForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])

    def test_payment_form_only_lists_owned_properties_and_units(self):
        form = PaymentForm(user=self.user)

        self.assertEqual(list(form.fields['property'].queryset), [self.own_property])
        self.assertEqual(list(form.fields['unit'].queryset), [self.own_unit])


class TenantPaginationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tenant-paginate', password='pass12345')
        self.client.force_login(self.user)

    def test_tenants_page_shows_pagination_controls(self):
        for index in range(15):
            Tenant.objects.create(
                first_name=f'User{index}',
                last_name='Example',
                phone_number=f'07000000{index}',
                next_of_kin_phone_number=f'07111111{index}',
            )

        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Rows')
        self.assertContains(response, 'per_page')


class TenantLedgerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ledger-owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Green Court',
            address='123 Main',
            county='Nairobi',
            total_units=1,
            description='Ledger property',
        )
        self.unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount='5000.00',
            description='Test unit',
        )
        self.same_property_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A2',
            rent_amount='6000.00',
            description='Same property unit',
        )
        self.tenant = Tenant.objects.create(
            first_name='Jane',
            last_name='Doe',
            phone_number='0712345678',
            next_of_kin_phone_number='0798765432',
            unit=self.unit,
            status='active',
        )
        self.same_property_tenant = Tenant.objects.create(
            first_name='John',
            last_name='Neighbor',
            phone_number='0712345679',
            next_of_kin_phone_number='0798765433',
            unit=self.same_property_unit,
            status='active',
        )
        self.other_property = Property.objects.create(
            user=self.user,
            name='Blue Court',
            address='456 Side',
            county='Nairobi',
            total_units=1,
            description='Other ledger property',
        )
        self.other_property_unit = Unit.objects.create(
            user=self.user,
            property=self.other_property,
            name='B1',
            rent_amount='7000.00',
            description='Other property unit',
        )
        self.other_property_tenant = Tenant.objects.create(
            first_name='Mary',
            last_name='Elsewhere',
            phone_number='0712345680',
            next_of_kin_phone_number='0798765434',
            unit=self.other_property_unit,
            status='active',
        )
        self.other_user = User.objects.create_user(username='ledger-other-owner', password='pass12345')
        self.unowned_property = Property.objects.create(
            user=self.other_user,
            name='Hidden Court',
            address='789 Away',
            county='Nairobi',
            total_units=1,
            description='Unowned ledger property',
        )
        self.unowned_unit = Unit.objects.create(
            user=self.other_user,
            property=self.unowned_property,
            name='C1',
            rent_amount='8000.00',
            description='Unowned unit',
        )
        self.unowned_tenant = Tenant.objects.create(
            first_name='Una',
            last_name='Hidden',
            phone_number='0712345681',
            next_of_kin_phone_number='0798765435',
            unit=self.unowned_unit,
            status='active',
        )
        self.invoice = Invoice.objects.create(
            user=self.user,
            unit=self.unit,
            tenant=self.tenant,
            amount='5000.00',
            due_date=date(2026, 7, 1),
            status='Unpaid',
        )
        self.payment = Payment.objects.create(
            user=self.user,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            code='RCT-2500',
            amount='2500.00',
            balance='2500.00',
            description='Partial rent payment',
            date=date(2026, 7, 2),
            status='claimed',
        )

    def test_ledger_page_displays_invoice_and_payment_entries(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.tenant.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tenant Ledger')
        self.assertContains(response, '<th>Code</th>', html=True)
        self.assertContains(response, 'RCT-2500')
        self.assertContains(response, 'Partial rent payment')
        self.assertContains(response, 'INV-')

    def test_ledger_tenant_switcher_only_lists_tenants_from_same_owned_property(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.tenant.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Change Tenant')
        self.assertContains(response, 'Jane Doe - A1')
        self.assertContains(response, 'John Neighbor - A2')
        self.assertNotContains(response, 'Mary Elsewhere - B1')
        self.assertNotContains(response, 'Una Hidden - C1')

    def test_ledger_blocks_tenants_from_other_users(self):
        response = self.client.get(reverse('tenants:tenant_ledger', args=[self.unowned_tenant.id]))

        self.assertEqual(response.status_code, 404)


class TenantListCleanupTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='cleanup-owner', password='pass12345')
        self.client.force_login(self.user)
        self.own_property = Property.objects.create(
            user=self.user,
            name='Own Property',
            address='1 Own Road',
            county='Nairobi',
            total_units=1,
            description='Owned property',
        )
        self.own_unit = Unit.objects.create(
            user=self.user,
            property=self.own_property,
            name='B1',
            rent_amount='3000.00',
            description='Owned unit',
        )
        self.other_user = User.objects.create_user(username='other-owner', password='pass12345')
        self.other_property = Property.objects.create(
            user=self.other_user,
            name='Other Property',
            address='2 Other Road',
            county='Nairobi',
            total_units=1,
            description='Other property',
        )
        self.other_unit = Unit.objects.create(
            user=self.other_user,
            property=self.other_property,
            name='C1',
            rent_amount='4000.00',
            description='Other unit',
        )

    def test_tenant_list_includes_orphans_and_limits_filters_to_owned_properties(self):
        Tenant.objects.create(
            first_name='Orphan',
            last_name='Tenant',
            phone_number='0710000000',
            next_of_kin_phone_number='0790000000',
        )
        Tenant.objects.create(
            first_name='Owned',
            last_name='Tenant',
            phone_number='0710000001',
            next_of_kin_phone_number='0790000001',
            unit=self.own_unit,
        )
        Tenant.objects.create(
            first_name='Other',
            last_name='Tenant',
            phone_number='0710000002',
            next_of_kin_phone_number='0790000002',
            unit=self.other_unit,
        )

        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Tenant.objects.filter(first_name='Orphan').exists())
        self.assertTrue(Tenant.objects.filter(first_name='Owned').exists())
        self.assertTrue(Tenant.objects.filter(first_name='Other').exists())
        self.assertContains(response, 'Owned Tenant')
        self.assertContains(response, 'Orphan Tenant')
        self.assertNotContains(response, 'Other Tenant')
        self.assertEqual(list(response.context['properties']), [self.own_property])

    def test_add_tenant_form_only_lists_owned_properties(self):
        response = self.client.get(reverse('tenants:tenant_list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['form'].fields['property'].queryset),
            [self.own_property],
        )

    def test_add_tenant_rejects_unowned_property(self):
        response = self.client.post(reverse('tenants:tenant_list'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'phone_number': '0712345678',
            'property': self.other_property.id,
            'next_of_kin_name': 'John Doe',
            'next_of_kin_phone_number': '0798765432',
            'description': '',
            'deposit_amount': '0.00',
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn('property', response.context['form'].errors)
        self.assertFalse(Tenant.objects.filter(first_name='Jane', last_name='Doe').exists())

    def test_available_units_requires_owned_property(self):
        own_response = self.client.get(reverse('tenants:available_units', args=[self.own_property.id]))
        other_response = self.client.get(reverse('tenants:available_units', args=[self.other_property.id]))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(own_response.json()['units'][0]['id'], self.own_unit.id)
        self.assertEqual(other_response.status_code, 404)


class TenantAttachDetachTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='attach-owner', password='pass12345')
        self.client.force_login(self.user)
        self.property = Property.objects.create(
            user=self.user,
            name='Attach Property',
            address='1 Attach Road',
            county='Nairobi',
            total_units=2,
            description='Property for attach/detach tests',
        )
        self.vacant_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A1',
            rent_amount='5000.00',
            status='vacant',
        )
        self.occupied_unit = Unit.objects.create(
            user=self.user,
            property=self.property,
            name='A2',
            rent_amount='6000.00',
            status='occupied',
        )
        self.unitless_tenant = Tenant.objects.create(
            first_name='Unitless',
            last_name='Tenant',
            phone_number='0710000000',
            next_of_kin_phone_number='0790000000',
        )
        self.unitful_tenant = Tenant.objects.create(
            first_name='Unitful',
            last_name='Tenant',
            phone_number='0710000001',
            next_of_kin_phone_number='0790000001',
            unit=self.occupied_unit,
        )
        Lease.objects.create(
            user=self.user,
            tenant=self.unitful_tenant,
            unit=self.occupied_unit,
            start_date=date.today(),
            monthly_rent='6000.00',
            deposit_held=0,
            is_active=True,
        )

    def test_upload_csv_with_no_vacant_units_creates_unitless_tenant(self):
        other_property = Property.objects.create(
            user=self.user,
            name='Full Property',
            address='2 Full Road',
            county='Nairobi',
            total_units=1,
            description='Property with no vacant units',
        )
        Unit.objects.create(
            user=self.user,
            property=other_property,
            name='B1',
            rent_amount='7000.00',
            status='occupied',
        )
        csv_file = SimpleUploadedFile(
            'tenants.csv',
            (
                'first_name,last_name,phone_number,property\n'
                'No,Unit,0710000002,Full Property\n'
            ).encode('utf-8'),
            content_type='text/csv',
        )

        response = self.client.post(reverse('tenants:upload_tenants'), {'file': csv_file})

        data = response.json()
        self.assertTrue(data['success'])
        tenant = Tenant.objects.get(first_name='No', last_name='Unit')
        self.assertIsNone(tenant.unit)
        self.assertContains(response, 'No vacant unit available')

    def test_attach_unit_endpoint(self):
        response = self.client.post(
            reverse('tenants:attach_tenant', args=[self.unitless_tenant.pk]),
            {'unit_id': self.vacant_unit.pk},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.unitless_tenant.refresh_from_db()
        self.assertEqual(self.unitless_tenant.unit, self.vacant_unit)
        self.vacant_unit.refresh_from_db()
        self.assertEqual(self.vacant_unit.status, 'occupied')

    def test_attach_unit_endpoint_rejects_non_vacant_unit(self):
        response = self.client.post(
            reverse('tenants:attach_tenant', args=[self.unitless_tenant.pk]),
            {'unit_id': self.occupied_unit.pk},
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])

    def test_detach_unit_endpoint(self):
        response = self.client.post(
            reverse('tenants:detach_tenant', args=[self.unitful_tenant.pk]),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.unitful_tenant.refresh_from_db()
        self.assertIsNone(self.unitful_tenant.unit)
        self.occupied_unit.refresh_from_db()
        self.assertEqual(self.occupied_unit.status, 'vacant')

    def test_attach_available_units_endpoint(self):
        response = self.client.get(
            reverse('tenants:attach_available_units'),
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        unit_ids = [u['id'] for u in data['units']]
        self.assertIn(self.vacant_unit.pk, unit_ids)
