"""
URL configuration for PROPATIA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views  # Import views from the current folder


app_name = 'tenants'  # Set the app name for namespacing

urlpatterns = [
    # Point to a view function, NOT an include()
    path('', views.tenant_list, name='tenant_list'),
    path('available-units/<int:pk>/', views.available_units, name='available_units'),
    path('attach-available-units/', views.attach_available_units, name='attach_available_units'),
    path('attach/<int:pk>/', views.attach_tenant, name='attach_tenant'),
    path('detach/<int:pk>/', views.detach_tenant, name='detach_tenant'),
    path('ledger/<int:pk>/', views.tenant_ledger, name='tenant_ledger'),
    path('delete/', views.delete_tenants, name='delete_tenants'),
    path('edit/<int:pk>/', views.edit_tenant, name='edit_tenant'),
    path('upload/', views.upload_tenants, name='upload_tenants'),
]