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

app_name = 'properties'  # Set the app name for namespacing

urlpatterns = [
    # Point to a view function, NOT an include()
    path('', views.property_list, name='properties_home'),
    path('edit/<int:pk>/', views.edit_property, name='edit_property'),
    path('delete/', views.delete_properties, name='delete_properties'),
]
