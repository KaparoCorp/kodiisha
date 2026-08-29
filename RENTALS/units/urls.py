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


app_name = 'units'  # Set the app name for namespacing

urlpatterns = [
    path('', views.units_list, name='units_list'),
    path('edit/<int:pk>/', views.edit_unit, name='edit_unit'),
    path('assign/<int:pk>/', views.assign_tenant, name='assign_tenant'),
    path('detach/<int:pk>/', views.detach_tenant, name='detach_tenant'),
    path('delete/', views.delete_units, name='delete_units'),
    path('related-data/', views.get_unit_related_data, name='get_unit_related_data'),
    path('upload/', views.upload_units, name='upload_units'),
    path('available-tenants/<int:pid>/', views.available_tenants, name='available_tenants'),
]