from django.contrib import admin
from .models import Route, Van


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'rent', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('route_name',)


@admin.register(Van)
class VanAdmin(admin.ModelAdmin):
    list_display = ('van_number', 'capacity', 'route', 'is_active', 'created_at')
    list_filter = ('is_active', 'route')
    search_fields = ('van_number',)
