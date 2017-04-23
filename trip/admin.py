# Django imports.
from django.contrib import admin

# Local imports.
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    fields = ('created', 'updated', 'pick_up_address', 'drop_off_address', 'status', 'riders',)
    readonly_fields = ('created', 'updated',)
    list_display = ('created', 'updated', 'pick_up_address', 'drop_off_address', 'status',)
    filter_horizontal = ('riders',)
