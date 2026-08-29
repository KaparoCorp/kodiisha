from django.shortcuts import render
from django.contrib.auth.decorators import login_required

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse

from django.db.models import Sum, Count
from properties.models import Property
from units.models import Unit
from invoices.models import Invoice
from payments.models import Payment
from water_bills.models import WaterBill
from arrears.models import Arrears
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties

@login_required
def report_generator(request):
    # 1. Get Filters
    property_id = request.GET.get('property')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # 2. Base Querysets (scoped to accessible properties)
    accessible_props = get_accessible_properties(request.user)
    properties = accessible_props
    units = Unit.objects.filter(property__in=accessible_props)
    invoices = Invoice.objects.filter(unit__property__in=accessible_props)
    payments = Payment.objects.filter(property__in=accessible_props)
    water_bills = WaterBill.objects.filter(unit__property__in=accessible_props)

    if property_id:
        units = units.filter(property_id=property_id)
        invoices = invoices.filter(unit__property_id=property_id)
        payments = payments.filter(property_id=property_id)
        water_bills = water_bills.filter(unit__property_id=property_id)

    if start_date:
        invoices = invoices.filter(due_date__gte=start_date)
        payments = payments.filter(date__gte=start_date)
        water_bills = water_bills.filter(due_date__gte=start_date)

    if end_date:
        invoices = invoices.filter(due_date__lte=end_date)
        payments = payments.filter(date__lte=end_date)
        water_bills = water_bills.filter(due_date__lte=end_date)

    # 3. Calculate Summary Stats
    total_units = units.count()
    occupied = units.filter(status='occupied').count()
    vacant = total_units - occupied
    
    rent_expected = invoices.filter(type='Rent').aggregate(Sum('amount'))['amount__sum'] or 0
    rent_collected = payments.aggregate(Sum('amount'))['amount__sum'] or 0
    water_total = water_bills.aggregate(Sum('amount'))['amount__sum'] or 0
    
    arrears = Arrears.objects.filter(unit__property__in=accessible_props)
    if property_id:
        arrears = arrears.filter(unit__property_id=property_id)
    if start_date:
        arrears = arrears.filter(date_marked__gte=start_date)
    if end_date:
        arrears = arrears.filter(date_marked__lte=end_date)
    total_arrears = arrears.aggregate(Sum('amount_due'))['amount_due__sum'] or 0
    
    collection_rate = 0
    if rent_expected > 0:
        collection_rate = (rent_collected / rent_expected) * 100

    recent_invoices = invoices.select_related('unit', 'tenant').order_by('-due_date')
    pagination = paginate_queryset(request, recent_invoices)

    context = {
        'properties': properties,
        'selected_property': property_id,
        'selected_start_date': start_date,
        'selected_end_date': end_date,
        'total_units': total_units,
        'occupied': occupied,
        'vacant': vacant,
        'collection_rate': round(collection_rate, 1),
        'rent_expected': rent_expected,
        'rent_collected': rent_collected,
        'water_total': water_total,
        'total_arrears': total_arrears,
        'recent_invoices': pagination['page_obj'],
    }
    context.update(pagination)
    return render(request, 'reports/report_view.html', context)
