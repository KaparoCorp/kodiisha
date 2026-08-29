from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views import View
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.access_utils import get_accessible_properties
from arrears.models import Arrears
from maintenance.models import Maintenance
from payments.models import Payment
from properties.models import Property
from tenants.models import Tenant
from water_bills.models import WaterBill


@login_required
def index(request):
    accessible_props = get_accessible_properties(request.user)
    acc_prop_ids = accessible_props.values_list('pk', flat=True)

    total_properties = accessible_props.count()
    total_tenants = Tenant.objects.filter(unit__property__in=accessible_props).count()
    active_tenants = Tenant.objects.filter(unit__property__in=accessible_props, status='active').count()
    inactive_tenants = Tenant.objects.filter(unit__property__in=accessible_props, status='inactive').count()

    all_prop_names = accessible_props.values_list('pk', 'name').order_by('name')
    tenant_stats_qs = accessible_props.annotate(
        active=Count('units__tenants', filter=Q(units__tenants__status='active'), distinct=True),
        inactive=Count('units__tenants', filter=Q(units__tenants__status='inactive'), distinct=True),
    ).values('pk', 'name', 'active', 'inactive')

    tenant_stats_map = {r['pk']: r for r in tenant_stats_qs}
    tenant_stats = [{'name': name, 'active': tenant_stats_map.get(pk, {}).get('active', 0), 'inactive': tenant_stats_map.get(pk, {}).get('inactive', 0)} for pk, name in all_prop_names]
    total_units = accessible_props.aggregate(total_units=Sum('total_units'))['total_units'] or 0

    property_breakdown = accessible_props.annotate(
        occupied_units_count=Count('units', filter=Q(units__status='occupied'))
    ).values('name', 'total_units', 'occupied_units_count').order_by('name')

    recent_properties_qs = accessible_props.select_related('user').prefetch_related('units')[:5]
    recent_properties = []
    for prop in recent_properties_qs:
        occupied_units = prop.units.filter(status='occupied').count()
        total_units_prop = prop.units.count() or prop.total_units
        recent_properties.append({
            'id': prop.id,
            'name': prop.name,
            'address': prop.address,
            'county': prop.county,
            'location': prop.address,
            'total_units': total_units_prop,
            'occupied_units': occupied_units,
            'description': prop.description,
            'property_image': prop.property_image.url if prop.property_image else '',
        })

    recent_tenants = Tenant.objects.filter(unit__property__in=accessible_props).select_related('unit', 'unit__property').order_by('-id')[:4]

    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    current_month_end = current_month_start.replace(day=monthrange(today.year, today.month)[1]) + timedelta(days=1)

    prev_month_end = current_month_start
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)

    revenue_by_property = (
        Payment.objects.filter(
            property__in=accessible_props,
            date__gte=current_month_start,
            date__lt=current_month_end,
        )
        .values('property__pk', 'property__name')
        .annotate(current_total=Sum('amount'))
    )

    prev_revenue_by_property = (
        Payment.objects.filter(
            property__in=accessible_props,
            date__gte=prev_month_start,
            date__lt=prev_month_end,
        )
        .values('property__pk', 'property__name')
        .annotate(prev_total=Sum('amount'))
    )

    revenue_map = {r['property__pk']: r['current_total'] or 0 for r in revenue_by_property}
    prev_revenue_map = {r['property__pk']: r['prev_total'] or 0 for r in prev_revenue_by_property}

    revenue_breakdown = []
    for pk, name in all_prop_names:
        current = revenue_map.get(pk, 0)
        previous = prev_revenue_map.get(pk, 0)
        pct = None
        if previous > 0:
            pct = float(round(((current - previous) / previous) * 100, 1))
        revenue_breakdown.append({
            'name': name,
            'amount': current,
            'percentage': pct,
            'abs_percentage': abs(pct) if pct is not None else None,
        })

    maint_by_property = (
        Maintenance.objects.filter(
            property__in=accessible_props,
            date__gte=current_month_start,
            date__lt=current_month_end,
        )
        .values('property__pk', 'property__name')
        .annotate(current_total=Sum('amount'))
    )

    prev_maint_by_property = (
        Maintenance.objects.filter(
            property__in=accessible_props,
            date__gte=prev_month_start,
            date__lt=prev_month_end,
        )
        .values('property__pk', 'property__name')
        .annotate(prev_total=Sum('amount'))
    )

    maint_map = {r['property__pk']: r['current_total'] or 0 for r in maint_by_property}
    prev_maint_map = {r['property__pk']: r['prev_total'] or 0 for r in prev_maint_by_property}

    maintenance_breakdown = []
    for pk, name in all_prop_names:
        current = maint_map.get(pk, 0)
        previous = prev_maint_map.get(pk, 0)
        pct = None
        if previous > 0:
            pct = float(round(((current - previous) / previous) * 100, 1))
        maintenance_breakdown.append({
            'name': name,
            'amount': current,
            'percentage': pct,
            'abs_percentage': abs(pct) if pct is not None else None,
        })

    arrears_by_property = (
        Arrears.objects.filter(
            unit__property__in=accessible_props,
            status='pending',
        )
        .values('unit__property__pk', 'unit__property__name')
        .annotate(total_arrears=Sum('amount_due'))
    )

    arrears_map = {r['unit__property__pk']: r['total_arrears'] or 0 for r in arrears_by_property}

    arrears_breakdown = []
    for pk, name in all_prop_names:
        arrears_breakdown.append({
            'name': name,
            'amount': arrears_map.get(pk, 0),
        })

    total_revenue = sum((item['amount'] for item in revenue_breakdown), Decimal('0'))
    total_maintenance = sum((item['amount'] for item in maintenance_breakdown), Decimal('0'))
    total_arrears = sum((item['amount'] for item in arrears_breakdown), Decimal('0'))

    water_bills_by_property = (
        WaterBill.objects.filter(
            unit__property__in=accessible_props,
            due_date__gte=current_month_start,
            due_date__lt=current_month_end,
        )
        .values('unit__property__pk', 'unit__property__name')
        .annotate(total_water=Sum('amount'))
    )
    water_bills_map = {r['unit__property__pk']: r['total_water'] or 0 for r in water_bills_by_property}
    water_bills_breakdown = []
    for pk, name in all_prop_names:
        water_bills_breakdown.append({
            'name': name,
            'amount': water_bills_map.get(pk, 0),
        })
    total_water_bills = sum((item['amount'] for item in water_bills_breakdown), Decimal('0'))

    context = {
        'total_properties': total_properties,
        'total_tenants': total_tenants,
        'active_tenants': active_tenants,
        'inactive_tenants': inactive_tenants,
        'tenant_stats': tenant_stats,
        'total_units': total_units,
        'recent_properties': recent_properties,
        'recent_tenants': recent_tenants,
        'total_revenue': total_revenue,
        'total_maintenance': total_maintenance,
        'total_arrears': total_arrears,
        'total_water_bills': total_water_bills,
        'revenue_breakdown': revenue_breakdown,
        'maintenance_breakdown': maintenance_breakdown,
        'property_breakdown': property_breakdown,
        'arrears_breakdown': arrears_breakdown,
        'water_bills_breakdown': water_bills_breakdown,
        'user_initial': request.user.first_name[0] + request.user.last_name[0] if request.user.is_authenticated and request.user.first_name and request.user.last_name else 'U',
        'user_name': f"{request.user.first_name} {request.user.last_name}" if request.user.is_authenticated and request.user.first_name else 'User'
    }

    return render(request, 'dashboard/dashboard.html', context)
