from django.urls import path
from . import views

app_name = 'ai_predictor'

urlpatterns = [
    path('insights/', views.ai_insights_view, name='insights'),
]
