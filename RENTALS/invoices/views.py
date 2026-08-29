from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Sum
from datetime import datetime
from decimal import Decimal

from .models import Invoice, InvoicePayment
from .services import allocate_credit_to_rent_invoice, create_invoices_for_units, set_payment_status_from_balance
from properties.models import Property
from units.models import Unit
from payments.models import Payment
from PROPATIA.pagination import paginate_queryset
from accounts.access_utils import get_accessible_properties
from arrears.views import sync_user_arrears

@login_required
def invoice_list(request):
    accessible_props = get_accessible_properties(request.user)
    acc_prop_ids = accessible_props.values_list('pk', flat=True)

    # Handle Single Invoice Generation
    if request.method == "POST" and 'single_generate' in request.POST:
        try:
            property_id = request.POST.get('property')
            unit_id = request.POST.get('unit')
            due_date_str = request.POST.get('due_date')
            inv_type = request.POST.get('type')
            
            if not property_id or not unit_id or not due_date_str or not inv_type:
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                    'properties': accessible_props,
                    'units': Unit.objects.filter(property__in=accessible_props),
                    'error': 'Please fill in all fields'
                })
            
            try:
                due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                    'properties': accessible_props,
                    'units': Unit.objects.filter(property__in=accessible_props),
                    'error': 'Please enter a valid due date in YYYY-MM-DD format'
                })

            property_obj = get_object_or_404(accessible_props, id=property_id)
            if not Unit.objects.filter(id=unit_id, property=property_obj).exists():
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                    'properties': accessible_props,
                    'units': Unit.objects.filter(property__in=accessible_props),
                    'error': 'Selected unit does not belong to the selected property'
                })
            unit = get_object_or_404(Unit, id=unit_id, property=property_obj)
            tenant = unit.get_assigned_tenant()

            if not tenant:
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                    'properties': accessible_props,
                    'units': Unit.objects.filter(property__in=accessible_props),
                    'error': f'No tenant found for unit {unit.name}'
                })

            created_invoices = create_invoices_for_units(
                request.user,
                [unit],
                due_date,
                inv_type=inv_type,
                apply_existing_credit=True,
            )

            if created_invoices:
                return redirect('invoices:invoice_list')
        
        except Exception as e:
            return render(request, 'invoices/invoices_view.html', {
                'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                'properties': accessible_props,
                'units': Unit.objects.filter(property__in=accessible_props),
                'error': f'Error creating invoice: {str(e)}'
            })
    
    # Handle Bulk Generation
    if request.method == "POST" and 'bulk_generate' in request.POST:
        prop_id = request.POST.get('property')
        due_date_str = request.POST.get('due_date')
        inv_type = request.POST.get('type')
        
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        except ValueError:
            return render(request, 'invoices/invoices_view.html', {
                'invoices': Invoice.objects.filter(unit__property__in=accessible_props).order_by('-due_date'),
                'properties': accessible_props,
                'units': Unit.objects.filter(property__in=accessible_props),
                'error': 'Please enter a valid due date in YYYY-MM-DD format'
            })
        
        units = Unit.objects.filter(property_id=prop_id, property__in=accessible_props)

        create_invoices_for_units(
            request.user,
            list(units),
            due_date,
            inv_type=inv_type,
            apply_existing_credit=True,
        )

        return redirect('invoices:invoice_list')

    invoices = Invoice.objects.filter(unit__property__in=accessible_props).select_related('unit', 'unit__property', 'tenant').order_by('due_date', 'id')
    selected_property = request.GET.get('property', '')
    selected_unit = request.GET.get('unit', '')
    selected_status = request.GET.get('status', '')
    selected_start_date = request.GET.get('start_date', '')
    selected_end_date = request.GET.get('end_date', '')
    selected_month = request.GET.get('month', '')

    if selected_property:
        invoices = invoices.filter(unit__property_id=selected_property)
    if selected_unit:
        invoices = invoices.filter(unit_id=selected_unit)
    if selected_status:
        invoices = invoices.filter(status=selected_status)
    if selected_start_date:
        invoices = invoices.filter(due_date__gte=selected_start_date)
    if selected_end_date:
        invoices = invoices.filter(due_date__lte=selected_end_date)

    if selected_month:
        try:
            year, month = selected_month.split('-')
            invoices = invoices.filter(due_date__year=year, due_date__month=month)
        except ValueError:
            selected_month = ''

    available_months = Invoice.objects.filter(unit__property__in=accessible_props).dates('due_date', 'month', order='DESC')

    pagination = paginate_queryset(request, invoices)

    context = {
        'invoices': pagination['page_obj'],
        'properties': accessible_props,
        'units': Unit.objects.filter(property__in=accessible_props),
        'selected_property': selected_property,
        'selected_unit': selected_unit,
        'selected_status': selected_status,
        'selected_start_date': selected_start_date,
        'selected_end_date': selected_end_date,
        'available_months': available_months,
        'selected_month': selected_month,
    }
    context.update(pagination)
    return render(request, 'invoices/invoices_view.html', context)


@login_required
def property_units(request, pk):
    """Return units for the selected property in the invoice form."""
    accessible_props = get_accessible_properties(request.user)
    property_obj = get_object_or_404(accessible_props, pk=pk)
    units = Unit.objects.filter(property=property_obj).order_by('name')

    return JsonResponse({
        'property': property_obj.name,
        'units': [
            {
                'id': unit.id,
                'name': unit.name,
                'rent_amount': float(unit.rent_amount),
                'tenant': unit.get_tenant_display_name() or '',
            }
            for unit in units
        ]
    })


@login_required
@require_POST
def delete_invoices(request):
    """Delete selected invoices.

    Before deleting, payment balances are restored so that payments which
    previously covered (fully or partially) the deleted invoices are made
    available as credit again.  Arrears are synced once after the
    transaction commits via ``transaction.on_commit`` — this avoids the
    ``database is locked`` errors that occurred when ``sync_user_arrears``
    was called from ``post_delete`` signal handlers *during* the cascade
    delete (every cascaded InvoicePayment fired its own sync with heavy
    read/write queries inside the delete transaction).
    """
    invoice_ids = request.POST.getlist('invoice_ids[]')

    if not invoice_ids:
        return JsonResponse({'success': False, 'message': 'No invoices selected'})

    accessible_props = get_accessible_properties(request.user)

    with transaction.atomic():
        # Resolve the concrete invoice IDs that are actually deletable
        # (scoped to properties the user can access).
        deletable_invoice_ids = list(
            Invoice.objects.filter(
                id__in=invoice_ids, unit__property__in=accessible_props
            ).values_list('id', flat=True)
        )

        if not deletable_invoice_ids:
            return JsonResponse({'success': False, 'message': 'No accessible invoices found'})

        # Restore payment balances for every InvoicePayment that will be
        # cascade-deleted.  We use ``update()`` (not ``save()``) so that the
        # Payment ``post_save`` signal — which would itself call
        # ``sync_user_arrears`` — is NOT triggered, avoiding lock contention.
        restorations = InvoicePayment.objects.filter(
            invoice_id__in=deletable_invoice_ids
        ).values('payment').annotate(total_to_restore=Sum('amount_applied'))

        for restoration in restorations:
            Payment.objects.filter(id=restoration['payment']).update(
                balance=F('balance') + Decimal(restoration['total_to_restore'])
            )

        deleted_count, _ = Invoice.objects.filter(
            id__in=deletable_invoice_ids
        ).delete()

    # Sync arrears *once*, after the transaction commits.  This runs outside
    # the delete transaction so it no longer competes for the write lock.
    transaction.on_commit(lambda: sync_user_arrears(request.user))

    return JsonResponse({
        'success': True,
        'message': f'Successfully deleted {deleted_count} invoice(s)'
    })


def get_invoice_payments(request):
    """Get available payments for an invoice (AJAX endpoint)"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    invoice_id = request.GET.get('invoice_id')
    
    if not invoice_id:
        return JsonResponse({'success': False, 'message': 'Invoice ID required'})
    
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Get unclaimed payments for the tenant of this invoice
        available_payments = Payment.objects.filter(
            tenant=invoice.tenant,
            status='unclaimed'
        ).values('id', 'amount', 'balance', 'date', 'code', 'description')
        
        # Calculate invoice balance
        remaining_balance = invoice.get_remaining_balance()
        
        return JsonResponse({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_amount': float(invoice.amount),
            'amount_paid': float(invoice.get_amount_paid()),
            'remaining_balance': float(remaining_balance),
            'payments': list(available_payments)
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_POST
def attach_payment_to_invoice(request):
    """Attach a payment to an invoice (handles partial payments)"""
    try:
        invoice_id = request.POST.get('invoice_id')
        payment_id = request.POST.get('payment_id')
        amount_to_apply = request.POST.get('amount_applied')
        
        if not all([invoice_id, payment_id, amount_to_apply]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        invoice = Invoice.objects.get(id=invoice_id)
        payment = Payment.objects.get(id=payment_id)
        
        # Validate payment belongs to invoice tenant
        if payment.tenant != invoice.tenant:
            return JsonResponse({'success': False, 'message': 'Payment does not match invoice tenant'})
        
        # Validate amount and convert to Decimal
        try:
            amount_applied = Decimal(str(amount_to_apply))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
        
        if amount_applied <= 0:
            return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})
        
        # Check if payment balance can cover this amount
        if amount_applied > payment.balance:
            return JsonResponse({'success': False, 'message': f'Payment remaining balance KES {payment.balance} is less than requested KES {amount_applied}'})
        if amount_applied > invoice.get_remaining_balance():
            return JsonResponse({'success': False, 'message': f'Invoice remaining balance KES {invoice.get_remaining_balance()} is less than requested KES {amount_applied}'})
        
        # Check if invoice attachment already exists
        existing = InvoicePayment.objects.filter(invoice=invoice, payment=payment).first()
        if existing:
            return JsonResponse({'success': False, 'message': 'Payment already attached to this invoice'})
        
        # Create the attachment
        invoice_payment = InvoicePayment.objects.create(
            invoice=invoice,
            payment=payment,
            amount_applied=amount_applied
        )
        
        # Update payment balance (now both are Decimal)
        payment.balance -= amount_applied
        
        # Update payment status to claimed only if balance is 0
        set_payment_status_from_balance(payment)
        
        # Update invoice status
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': f'Payment of KES {amount_applied} attached successfully',
            'remaining_balance': float(invoice.get_remaining_balance()),
            'payment_remaining': float(payment.balance),
            'new_status': invoice.status
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


def get_attached_payments(request):
    """Get all attached payments for an invoice"""
    try:
        invoice_id = request.GET.get('invoice_id')
        
        if not invoice_id:
            return JsonResponse({'success': False, 'message': 'Invoice ID is required'})
        
        invoice = Invoice.objects.get(id=invoice_id)
        attached_payments = InvoicePayment.objects.filter(invoice=invoice).select_related('payment')
        
        payments_list = []
        for ip in attached_payments:
            payments_list.append({
                'invoice_payment_id': ip.id,
                'amount': float(ip.payment.amount),
                'amount_applied': float(ip.amount_applied),
                'date': ip.payment.date.strftime('%Y-%m-%d'),
                'description': ip.payment.description or ''
            })
        
        return JsonResponse({
            'success': True,
            'attached_payments': payments_list
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


def _check_user_permission(user):
    """Check if user is admin or landlord"""
    if user is None or not user.is_authenticated:
        return False
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(user=user)
        return profile.role in ['admin', 'landlord']
    except:
        return False


@require_POST
def update_invoice_payment(request):
    """Update amount applied for an invoice payment"""
    try:
        # Check permission
        if not _check_user_permission(request.user):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        invoice_payment_id = request.POST.get('invoice_payment_id')
        new_amount = request.POST.get('amount_applied')
        
        if not invoice_payment_id or not new_amount:
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        new_amount = Decimal(str(new_amount))
        invoice_payment = InvoicePayment.objects.get(id=invoice_payment_id)
        
        # Calculate the difference
        old_amount = invoice_payment.amount_applied
        difference = new_amount - old_amount
        invoice = invoice_payment.invoice
        invoice_remaining_without_this_payment = invoice.get_remaining_balance() + old_amount

        if new_amount <= 0:
            return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})

        # Do not let an edit overpay the invoice.
        if new_amount > invoice_remaining_without_this_payment:
            return JsonResponse({
                'success': False,
                'message': f'Invoice only has KES {invoice_remaining_without_this_payment} available for this payment'
            })
        
        # Check if payment has enough balance
        if difference > 0:
            if invoice_payment.payment.balance < difference:
                return JsonResponse({
                    'success': False, 
                    'message': f'Payment only has KES {invoice_payment.payment.balance} remaining'
                })
        
        # Update invoice payment amount
        invoice_payment.amount_applied = new_amount
        invoice_payment.save()
        
        # Update payment balance
        payment = invoice_payment.payment
        payment.balance -= difference

        set_payment_status_from_balance(payment)
        
        # Update invoice status
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment amount updated successfully'
        })
    
    except InvoicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_POST
def remove_invoice_payment(request):
    """Remove an invoice payment attachment"""
    try:
        # Check permission
        if not _check_user_permission(request.user):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        invoice_payment_id = request.POST.get('invoice_payment_id')
        
        if not invoice_payment_id:
            return JsonResponse({'success': False, 'message': 'Invoice payment ID is required'})
        
        invoice_payment = InvoicePayment.objects.get(id=invoice_payment_id)
        
        # Get the amount before deletion
        amount_applied = invoice_payment.amount_applied
        payment = invoice_payment.payment
        invoice = invoice_payment.invoice
        
        # Delete the attachment
        invoice_payment.delete()
        
        # Restore payment balance
        payment.balance += amount_applied
        set_payment_status_from_balance(payment)
        
        # Update invoice status
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment removed successfully'
        })
    
    except InvoicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
