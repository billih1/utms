from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('collection/', views.monthly_collection, name='monthly_collection'),
    path('due/', views.due_remaining, name='due_remaining'),
    path('defaulters/', views.defaulter_report, name='defaulter_report'),
    path('export/excel/', views.export_excel, name='export_excel'),
]
