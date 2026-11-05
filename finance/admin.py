from django.contrib import admin
from .models import FeePayment, Voucher, Challan, Receipt


@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'month', 'amount', 'amount_paid', 'status', 'paid_at')
    list_filter = ('month', 'status')
    search_fields = ('student__admission_number', 'student__name')


@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = ('voucher_number', 'fee_payment', 'issue_date')
    search_fields = ('voucher_number',)


@admin.register(Challan)
class ChallanAdmin(admin.ModelAdmin):
    list_display = ('challan_number', 'fee_payment', 'bank_office_ref', 'issue_date')
    search_fields = ('challan_number',)


@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'fee_payment', 'printed_at')
    search_fields = ('receipt_number',)
