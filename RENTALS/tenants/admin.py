from django.contrib import admin
from tenants.models import Tenant


# Register your models here.
admin.site.register(Tenant)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('unit', 'first_name', 'last_name', 'phone_number', 'total_units', 'description', 'status', 'created_at', 'updated_at')
    list_filter = ('unit', 'first_name')