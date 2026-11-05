from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    path('driver-panel/', views.driver_panel, name='driver_panel'),
    path('logs/', views.vehicle_log_list, name='vehicle_log_list'),
]
