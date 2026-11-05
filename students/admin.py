from django.contrib import admin
from .models import Student


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('admission_number', 'name', 'program', 'semester', 'route', 'van', 'is_active')
    list_filter = ('program', 'semester', 'route', 'is_active')
    search_fields = ('admission_number', 'name', 'phone')
