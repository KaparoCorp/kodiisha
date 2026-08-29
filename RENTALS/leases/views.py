from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Lease
from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from django.contrib.auth.decorators import login_required
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties

@login_required
def index(request):
    accessible_props = get_accessible_properties(request.user)

    leases = Lease.objects.filter(
        unit__property__in=accessible_props,
        is_active=True
    ).select_related('tenant', 'unit', 'unit__property').order_by('unit__property__name', 'unit__name')
    
    selected_property = request.GET.get('property', '')
    selected_unit = request.GET.get('unit', '')

    properties = accessible_props.order_by('name')
    allowed_property_ids = set(properties.values_list('id', flat=True))

    if selected_property and selected_property.isdigit() and int(selected_property) in allowed_property_ids:
        leases = leases.filter(unit__property_id=selected_property)
    else:
        selected_property = ''

    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')
    if selected_property:
        units = units.filter(property_id=selected_property)

    allowed_unit_ids = set(units.values_list('id', flat=True))
    if selected_unit and selected_unit.isdigit() and int(selected_unit) in allowed_unit_ids:
        leases = leases.filter(unit_id=selected_unit)
    else:
        selected_unit = ''

    pagination = paginate_queryset(request, leases)
    
    context = {
        'leases': pagination['page_obj'],
        'properties': properties,
        'units': units,
        'selected_property': selected_property,
        'selected_unit': selected_unit,
        'today': timezone.now().date(),
    }
    context.update(pagination)
    return render(request, 'leases/leases_view.html', context)


@login_required
def units_for_property(request):
    accessible_props = get_accessible_properties(request.user)
    property_id = request.GET.get('property', '')
    units = Unit.objects.filter(property__in=accessible_props).select_related('property').order_by('property__name', 'name')

    if property_id:
        if not property_id.isdigit() or not accessible_props.filter(id=property_id).exists():
            return JsonResponse({'units': []})
        units = units.filter(property_id=property_id)

    unit_options = [
        {
            'id': unit.id,
            'name': unit.name,
            'property': unit.property.name,
        }
        for unit in units
    ]
    return JsonResponse({'units': unit_options})


@login_required
def tenants_for_unit(request):
    accessible_props = get_accessible_properties(request.user)
    unit_id = request.GET.get('unit', '')
    tenants = Tenant.objects.filter(unit__property__in=accessible_props)

    if unit_id:
        if not unit_id.isdigit():
            return JsonResponse({'tenants': []})
        tenants = tenants.filter(unit_id=unit_id)

    tenants = tenants.exclude(leases__is_active=True).order_by('last_name', 'first_name')

    tenant_options = [
        {
            'id': t.id,
            'first_name': t.first_name,
            'last_name': t.last_name,
        }
        for t in tenants
    ]
    return JsonResponse({'tenants': tenant_options})


@login_required
def create_lease(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})

    unit_id = request.POST.get('unit_id')
    tenant_id = request.POST.get('tenant_id')
    start_date_str = request.POST.get('start_date', '')
    deposit_held_str = request.POST.get('deposit_held', '0')

    if not unit_id or not tenant_id:
        return JsonResponse({'success': False, 'message': 'Unit and tenant are required'})

    accessible_props = get_accessible_properties(request.user)
    unit = get_object_or_404(Unit, pk=unit_id, property__in=accessible_props)
    tenant = get_object_or_404(Tenant, pk=tenant_id, unit=unit)

    if Lease.objects.filter(unit=unit, is_active=True).exists():
        return JsonResponse({'success': False, 'message': f'Unit {unit.name} already has an active lease'})

    if tenant.leases.filter(is_active=True).exists():
        return JsonResponse({'success': False, 'message': f'{tenant.first_name} {tenant.last_name} already has an active lease'})

    try:
        start_date = timezone.now().date()
        if start_date_str:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'message': 'Invalid start date format'})

    try:
        deposit_held = float(deposit_held_str)
    except (ValueError, TypeError):
        deposit_held = 0

    lease = Lease.objects.create(
        user=request.user,
        tenant=tenant,
        unit=unit,
        start_date=start_date,
        monthly_rent=unit.rent_amount,
        deposit_held=deposit_held,
        is_active=True,
    )

    tenant.unit = unit
    tenant.save()
    unit.status = 'occupied'
    unit.save()

    return JsonResponse({'success': True, 'message': f'Lease created for {tenant.first_name} {tenant.last_name} in {unit.name}'})
