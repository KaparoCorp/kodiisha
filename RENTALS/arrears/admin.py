from django.contrib import admin
from .models import Arrears


@admin.register(Arrears)
class ArrearsAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'tenant', 'amount_due', 'days_overdue', 'status', 'date_marked')
    list_filter = ('status', 'date_marked', 'user')
    search_fields = ('tenant__first_name', 'tenant__last_name', 'invoice__invoice_number')
    readonly_fields = ('date_marked', 'date_resolved')
    fieldsets = (
        ('Arrears Information', {
            'fields': ('invoice', 'tenant', 'unit', 'user')
        }),
        ('Amount & Days', {
            'fields': ('amount_due', 'days_overdue')
        }),
        ('Status & Dates', {
            'fields': ('status', 'date_marked', 'date_resolved')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )
    actions = ['mark_resolved']

    def mark_resolved(self, request, queryset):
        updated = 0
        for arrears in queryset:
            if arrears.status != 'resolved':
                arrears.mark_resolved()
                updated += 1
        self.message_user(request, f'Marked {updated} arrears record(s) as resolved.')
    
    mark_resolved.short_description = 'Mark selected arrears as resolved'

