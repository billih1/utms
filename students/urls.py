from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    path('', views.student_list, name='student_list'),
    path('create/', views.student_create, name='student_create'),
    path('import/', views.student_import, name='student_import'),
    path('<int:pk>/', views.student_detail, name='student_detail'),
    path('<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('<int:pk>/delete/', views.student_delete, name='student_delete'),
    path('<int:pk>/assign/', views.student_assign, name='student_assign'),
    path('vans-for-route/<int:route_id>/', views.get_vans_for_route, name='get_vans_for_route'),
]
