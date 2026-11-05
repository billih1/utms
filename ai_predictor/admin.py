from django.contrib import admin
from .models import Prediction


@admin.register(Prediction)
class PredictionAdmin(admin.ModelAdmin):
    list_display = ('student', 'target_month', 'risk_score', 'risk_level', 'predicted_at')
    list_filter = ('risk_level', 'target_month')
    search_fields = ('student__admission_number', 'student__name')
