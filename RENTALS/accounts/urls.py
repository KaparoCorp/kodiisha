from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('invitations/', views.invitations_view, name='invitations'),
    path('invitations/delete/<int:pk>/', views.delete_invitation, name='delete_invitation'),
    path('invitations/accept/<uuid:token>/', views.accept_invitation_view, name='accept_invitation'),
    
    # Settings & Profile
    path('settings/', views.profile_settings, name='profile_settings'),
    path('support/', views.support_view, name='support'),
    path('delete/', views.delete_account_view, name='delete_account'),
    
    # Password Management (Built-in Django views)
    path('password-change/', auth_views.PasswordChangeView.as_view(template_name='accounts/password_change.html'), name='change_password'),
    path('password-change/', 
        auth_views.PasswordChangeView.as_view(
            template_name='accounts/password_change.html',
            # This line fixes the error by directing to your login name
            success_url=reverse_lazy('accounts:login') 
        ), 
        name='change_password'),#    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='accounts/password_change_done.html'), name='password_change_done'),
    path('audit-log/', views.audit_log_view, name='audit_log'),
]
