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
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'),  # This is the root URL
    path('dashboard/', include('dashboard.urls'),name='dashboard'),
    path('arrears/', include('arrears.urls'), name='arrears'),
    path('units/', include('units.urls'), name='units'),
    path('leases/', include('leases.urls'), name='leases'),
    path('invoices/', include('invoices.urls'), name='invoices'),
    path('payments/', include('payments.urls'), name='payments'),
    path('reports/', include('reports.urls'), name='reports'), 
    path('tenants/', include('tenants.urls'), name='tenants'),
    path('properties/', include('properties.urls'), name='properties'),
    path('maintenance/', include('maintenance.urls'), name='maintenance'),
    path('accounts/', include('accounts.urls'), name='accounts'),
    path('water_bills/', include('water_bills.urls', namespace='water_bills')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
