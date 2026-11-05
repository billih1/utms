from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    path('fees/', views.fee_list, name='fee_list'),
    path('generate-dues/', views.generate_dues_view, name='generate_dues'),
    path('challans/bulk-print/', views.bulk_print_challans, name='bulk_print_challans'),
    path('vouchers/bulk-print/', views.bulk_print_vouchers, name='bulk_print_vouchers'),
    path('voucher/<int:pk>/generate/', views.generate_voucher_view, name='generate_voucher'),
    path('voucher/<int:pk>/print/', views.print_voucher, name='print_voucher'),
    path('challan/<int:pk>/generate/', views.generate_challan_view, name='generate_challan'),
    path('challan/<int:pk>/print/', views.print_challan, name='print_challan'),
    path('payment/<int:pk>/mark-paid/', views.mark_paid_view, name='mark_paid'),
    path('receipt/<int:pk>/print/', views.print_receipt, name='print_receipt'),
]
