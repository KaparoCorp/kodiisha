from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.db.models import DateField
from django.db import transaction
from django.utils import timezone
from collections import OrderedDict
import threading

from units.models import Unit
from tenants.models import Tenant
from invoices.models import Invoice
from .models import Arrears
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties

_sync_tenant_ids = threading.local()


def _get_synced_tenant_ids():
    if not hasattr(_sync_tenant_ids, 'ids'):
        _sync_tenant_ids.ids = set()
    return _sync_tenant_ids.ids


def _clear_synced_tenants():
    if hasattr(_sync_tenant_ids, 'ids'):
        _sync_tenant_ids.ids.clear()


def sync_user_arrears(user, tenant=None):
    """Keep arrears records aligned with currently overdue invoices.

    When ``tenant`` is provided, only invoices for that tenant are considered,
    which scopes the sync to the affected tenant and avoids scanning all tenants
    accessible to the user.
    """
    synced_ids = _get_synced_tenant_ids()

    if tenant and tenant.id in synced_ids:
        return

    today = timezone.now().date()
    accessible_props = get_accessible_properties(user)
    overdue_invoices = Invoice.objects.filter(
        unit__property__in=accessible_props,
        due_date__lt=today,
        status__in=['Unpaid', 'Partially Paid'],
    ).select_related('tenant', 'unit', 'user').prefetch_related('invoice_payments')

    if tenant:
        overdue_invoices = overdue_invoices.filter(tenant=tenant)

    active_invoice_ids = []
    synced_tenant_ids = set()
    for invoice in overdue_invoices:
        remaining_balance = invoice.get_remaining_balance()
        if remaining_balance <= 0:
            continue

        active_invoice_ids.append(invoice.id)
        synced_tenant_ids.add(invoice.tenant_id)
        days_overdue = (today - invoice.due_date).days
        arrears_record, _created = Arrears.objects.get_or_create(
            invoice=invoice,
            tenant=invoice.tenant,
            defaults={
                'tenant': invoice.tenant,
                'unit': invoice.unit,
                'user': invoice.user,
                'amount_due': remaining_balance,
                'days_overdue': days_overdue,
                'status': 'pending',
            }
        )

        arrears_record.user = invoice.user
        arrears_record.tenant = invoice.tenant
        arrears_record.unit = invoice.unit
        arrears_record.amount_due = remaining_balance
        arrears_record.days_overdue = days_overdue
        if arrears_record.status == 'resolved':
            arrears_record.status = 'pending'
            arrears_record.date_resolved = None
        arrears_record.save()

    resolved_records = Arrears.objects.filter(
        user=user,
        status='pending',
    )
    if tenant:
        resolved_records = resolved_records.filter(tenant=tenant)
    resolved_records = resolved_records.exclude(invoice_id__in=active_invoice_ids)
    for arrears_record in resolved_records:
        arrears_record.amount_due = 0
        arrears_record.mark_resolved()

    synced_ids.update(synced_tenant_ids)
    transaction.on_commit(_clear_synced_tenants)


@login_required
def arrears_report(request):
    sync_user_arrears(request.user)
    accessible_props = get_accessible_properties(request.user)

    # 1. Get filter parameters
    prop_id = request.GET.get('property')
    unit_id = request.GET.get('unit')
    tenant_id = request.GET.get('tenant')
    status_filter = request.GET.get('status', 'all')
    selected_start_date = request.GET.get('start_date', '')
    selected_end_date = request.GET.get('end_date', '')

    # 2. Base Query: Start with Arrears records (scoped to accessible properties)
    arrears_records = Arrears.objects.filter(
        unit__property__in=accessible_props
    ).select_related(
        'invoice', 'tenant', 'unit', 'unit__property'
    ).order_by('-date_marked')

    # 3. Apply Filters
    if prop_id:
        arrears_records = arrears_records.filter(unit__property_id=prop_id)
    if unit_id:
        arrears_records = arrears_records.filter(unit_id=unit_id)
    if tenant_id:
        arrears_records = arrears_records.filter(tenant_id=tenant_id)
    
    # Filter by status (default to pending)
    if status_filter and status_filter != 'all':
        arrears_records = arrears_records.filter(status=status_filter)
    if selected_start_date:
        arrears_records = arrears_records.filter(date_marked__gte=selected_start_date)
    if selected_end_date:
        arrears_records = arrears_records.filter(date_marked__lte=selected_end_date)

    agg_results = arrears_records.aggregate(
        total_arrears=Sum('amount_due', filter=Q(status='pending')),
        total_records=Count('id'),
    )
    total_arrears_amount = agg_results['total_arrears'] or 0
    total_records = agg_results['total_records'] or 0

    monthly_groups = OrderedDict()
    tenant_running_totals = {}
    pending_arrears = arrears_records.filter(status='pending').select_related('tenant', 'unit', 'invoice')
    monthly_source = list(pending_arrears.annotate(
        month=TruncMonth('invoice__due_date', output_field=DateField())
    ).order_by('tenant__last_name', 'tenant__first_name', 'month', 'id'))

    tenant_ids = {record.tenant_id for record in monthly_source}
    unit_ids = {record.unit_id for record in monthly_source}
    tenants = Tenant.objects.filter(id__in=tenant_ids).in_bulk()
    units = Unit.objects.filter(id__in=unit_ids).in_bulk()

    for record in monthly_source:
        key = (record.tenant_id, record.unit_id, record.month)
        if key not in monthly_groups:
            tenant_obj = tenants.get(record.tenant_id)
            unit_obj = units.get(record.unit_id)
            monthly_groups[key] = {
                'tenant': tenant_obj,
                'unit': unit_obj,
                'month': record.month,
                'monthly_arrears': 0,
                'accumulated_arrears': 0,
            }
        monthly_groups[key]['monthly_arrears'] += record.amount_due

    monthly_arrears = []
    for group in monthly_groups.values():
        if group['tenant']:
            tenant_id = group['tenant'].id
            tenant_running_totals[tenant_id] = tenant_running_totals.get(tenant_id, 0) + group['monthly_arrears']
            group['accumulated_arrears'] = tenant_running_totals[tenant_id]
        monthly_arrears.append(group)

    pagination = paginate_queryset(request, arrears_records)

    # 5. Get available filter options (scoped to accessible properties)
    properties = accessible_props
    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')
    if prop_id:
        units = units.filter(property_id=prop_id)
    tenants = Tenant.objects.filter(unit__property__in=accessible_props, status='active').order_by('first_name', 'last_name')
    if prop_id:
        tenants = tenants.filter(unit__property_id=prop_id)

    # 6. Context
    context = {
        'report_data': pagination['page_obj'],
        'page_obj': pagination['page_obj'],
        'total_arrears_amount': total_arrears_amount,
        'total_records': total_records,
        'monthly_arrears': monthly_arrears,
        'properties': properties,
        'units': units,
        'tenants': tenants,
        'selected_property': prop_id,
        'selected_unit': unit_id,
        'selected_tenant': tenant_id,
        'selected_status': status_filter,
        'selected_start_date': selected_start_date,
        'selected_end_date': selected_end_date,
        'title': 'Arrears Report'
    }
    context.update(pagination)

    return render(request, 'arrears/arrears_report.html', context)
