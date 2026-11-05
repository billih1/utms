from django.urls import path
from . import views

app_name = 'transport'

urlpatterns = [
    path('routes/', views.route_list, name='route_list'),
    path('routes/create/', views.route_create, name='route_create'),
    path('routes/<int:pk>/edit/', views.route_edit, name='route_edit'),
    path('routes/<int:pk>/delete/', views.route_delete, name='route_delete'),
    path('vans/', views.van_list, name='van_list'),
    path('vans/create/', views.van_create, name='van_create'),
    path('vans/<int:pk>/edit/', views.van_edit, name='van_edit'),
    path('vans/<int:pk>/delete/', views.van_delete, name='van_delete'),
]
