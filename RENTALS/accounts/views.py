from datetime import timedelta
import logging

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator

from .forms import InvitationAcceptForm, InvitationCreateForm, UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .models import Invitation, Profile, PropertyAccess, AuditLog
from .emails import send_invitation_email
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)



def register_view(request):
    form = UserRegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({"success": True, "redirect_url": "/accounts/login/"})
            else:
                return redirect('accounts:login')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                # Send back the form HTML with errors
                from django.template.loader import render_to_string
                form_html = render_to_string('accounts/register_form.html', {'form': form}, request=request)
                return JsonResponse({"success": False, "form_html": form_html}, status=400)
            
    return render(request, 'accounts/register.html', {'form': form})


def _is_app_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == Profile.ADMIN


def _invitation_url(request, invitation):
    return request.build_absolute_uri(reverse('accounts:accept_invitation', args=[invitation.token]))


@login_required
def invitations_view(request):
    if not _is_app_admin(request.user):
        messages.error(request, 'Only admins can manage invitations.')
        return redirect('dashboard_home')

    created_invite_url = None
    if request.method == 'POST':
        form = InvitationCreateForm(request.POST, user=request.user)
        if form.is_valid():
            invitation = form.save(commit=False)
            invitation.invited_by = request.user
            invitation.expires_at = timezone.now() + timedelta(days=7)
            invitation.save()
            form.save_m2m()  # Save the M2M properties
            created_invite_url = _invitation_url(request, invitation)
            messages.success(request, 'Invitation created. Share the link with the invited user.')
            send_invitation_email(invitation, created_invite_url)
            form = InvitationCreateForm(user=request.user)
    else:
        form = InvitationCreateForm(user=request.user)

    invitations = Invitation.objects.filter(invited_by=request.user).select_related('invited_by').prefetch_related('properties')
    for invitation in invitations:
        invitation.mark_expired()

    return render(request, 'accounts/invitations.html', {
        'form': form,
        'invitations': invitations,
        'created_invite_url': created_invite_url,
        'title': 'Invitations',
    })


def accept_invitation_view(request, token):
    invitation = get_object_or_404(Invitation.objects.prefetch_related('properties'), token=token)
    if not invitation.can_accept():
        invitation.mark_expired()
        return render(request, 'accounts/invitation_invalid.html', {
            'invitation': invitation,
            'title': 'Invitation unavailable',
        }, status=410)

    if request.method == 'POST':
        form = InvitationAcceptForm(request.POST, invitation=invitation)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = invitation.email
            user.first_name = form.cleaned_data.get('first_name') or invitation.first_name
            user.last_name = form.cleaned_data.get('last_name') or invitation.last_name
            user.save()
            user.profile.role = invitation.role
            user.profile.save()

            # Grant property access to the new user
            for prop in invitation.properties.all():
                PropertyAccess.objects.create(
                    user=user,
                    property=prop,
                    granted_by=invitation.invited_by,
                )

            invitation.status = Invitation.ACCEPTED
            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=['status', 'accepted_at'])
            login(request, user)
            messages.success(request, 'Your account has been created.')
            return redirect('dashboard_home')
    else:
        form = InvitationAcceptForm(invitation=invitation)

    return render(request, 'accounts/accept_invitation.html', {
        'form': form,
        'invitation': invitation,
        'title': 'Accept Invitation',
    })

@login_required
@require_POST
def delete_invitation(request, pk):
    """Delete an invitation (admin only)."""
    if not _is_app_admin(request.user):
        return JsonResponse({'success': False, 'message': 'Only admins can delete invitations.'}, status=403)
    invitation = get_object_or_404(Invitation, pk=pk, invited_by=request.user)
    invitation.delete()
    messages.success(request, f'Invitation for {invitation.email} has been deleted.')
    return JsonResponse({'success': True})


@login_required
def profile_settings(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('accounts:profile_settings')
    else:
        # Applying placeholders directly to the form instances if they aren't in forms.py
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form, 
        'p_form': p_form,
        'title': 'Account Settings'
    }
    return render(request, 'accounts/accounts_view.html', context)

@login_required
def delete_account_view(request):
    if request.method == 'POST':
        user = request.user
        logout(request) # Log out before deleting to clear session
        user.delete()
        messages.warning(request, 'Your account has been permanently deleted.')
        return redirect('accounts:login') # Redirect to login as profile no longer exists
    return render(request, 'accounts/delete_confirm.html')

def support_view(request):
    return render(request, 'accounts/support.html', {'title': 'Support'})

def password_change_done(request):
    return render(request, 'accounts/password_change_done.html', {'title': 'Password Changed'})


@login_required
def audit_log_view(request):
    if not (request.user.is_superuser or (hasattr(request.user, 'profile') and request.user.profile.role in [Profile.ADMIN, Profile.LANDLORD])):
        messages.error(request, 'Only admins and landlords can view audit logs.')
        return redirect('dashboard_home')

    logs = AuditLog.objects.select_related('user', 'user__profile').all()

    user_id = request.GET.get('user')
    action = request.GET.get('action')
    model_name = request.GET.get('model')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if user_id:
        logs = logs.filter(user_id=user_id)
    if action:
        logs = logs.filter(action=action)
    if model_name:
        logs = logs.filter(model_name=model_name)
    if start_date:
        logs = logs.filter(timestamp__date__gte=start_date)
    if end_date:
        logs = logs.filter(timestamp__date__lte=end_date)

    logs = logs.order_by('-timestamp')
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    users_with_logs = User.objects.filter(id__in=AuditLog.objects.values_list('user_id', flat=True).distinct())

    context = {
        'logs': page_obj,
        'title': 'Audit Log',
        'action_choices': AuditLog.ACTION_CHOICES,
        'users_with_logs': users_with_logs,
        'selected_user': user_id or '',
        'selected_action': action or '',
        'selected_model': model_name or '',
        'selected_start_date': start_date or '',
        'selected_end_date': end_date or '',
    }
    return render(request, 'accounts/audit_log.html', context)
