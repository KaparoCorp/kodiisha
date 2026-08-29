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
from . import views

app_name = 'maintenance'

urlpatterns = [
    path('', views.index, name='maintenance_home'),
    path('create/', views.create_maintenance, name='create_maintenance'),
    path('toggle-status/<int:pk>/', views.toggle_status, name='toggle_status'),
    path('attach-receipt/<int:pk>/', views.attach_receipt, name='attach_receipt'),
    path('completed/', views.completed_maintenance, name='completed_maintenance'),
    path('delete/', views.delete_maintenance, name='delete_maintenance'),
    path('edit/<int:pk>/', views.edit_maintenance, name='edit_maintenance'),
    path('property-units/<int:pk>/', views.property_units, name='property_units'),
]
