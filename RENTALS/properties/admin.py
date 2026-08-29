from django.contrib import admin

# Register your models here.
from .models import Property


@admin.register(Property)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'address', 'county', 'total_units', 'description', 'property_image', 'created_at', 'updated_at')
    list_filter = ('name', 'user')