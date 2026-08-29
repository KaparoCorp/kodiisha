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

app_name = 'water_bills'

urlpatterns = [
    # Point to a view function, NOT an include()
    path('', views.water_bill_list, name='water_bills_home'),
    path('claim-payment/', views.claim_payment_for_water, name='claim_payment_for_water'),
    path('available-payments/', views.get_available_payments_for_water_claim, name='available_payments_for_water_claim'),
    path('delete/', views.delete_water_bills, name='delete_water_bills'),
    path('bulk-generate/', views.bulk_generate_water_bills, name='bulk_generate_water_bills'),
    path('payments/', views.water_bill_payment_list, name='water_bill_payments'),
    path('payments/delete/', views.delete_water_bill_payments, name='delete_water_bill_payments'),
    path('upload/', views.upload_water_bill_payments, name='upload_water_bill_payments'),
    path('edit/<int:pk>/', views.edit_water_bill, name='edit_water_bill'),
    path('delete/<int:pk>/', views.delete_water_bill, name='delete_water_bill'),
    path('property-units/<int:pk>/', views.property_units, name='property_units'),
]
