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


app_name = 'invoices'  # Set the app name for namespacing
urlpatterns = [
    # Point to a view function, NOT an include()
    path('', views.invoice_list, name='invoice_list'),
    path('property-units/<int:pk>/', views.property_units, name='property_units'),
    path('delete/', views.delete_invoices, name='delete_invoices'),
    path('get-payments/', views.get_invoice_payments, name='get_payments'),
    path('attach-payment/', views.attach_payment_to_invoice, name='attach_payment'),
    path('get-attached-payments/', views.get_attached_payments, name='get_attached_payments'),
    path('update-invoice-payment/', views.update_invoice_payment, name='update_invoice_payment'),
    path('remove-invoice-payment/', views.remove_invoice_payment, name='remove_invoice_payment'),
]
