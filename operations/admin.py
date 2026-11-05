from django.contrib import admin
from .models import VehicleLog


@admin.register(VehicleLog)
class VehicleLogAdmin(admin.ModelAdmin):
    list_display = ('van', 'route', 'driver', 'date', 'departure_time', 'arrival_time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('van__van_number', 'driver__username')
