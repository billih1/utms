from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from accounts.decorators import accountant_required
from students.models import Student
from .models import FeePayment, Voucher, Challan, Receipt
from .forms import GenerateDuesForm, PaymentRecordForm
from .services import generate_monthly_dues, get_or_create_voucher, get_or_create_challan, record_payment


@accountant_required
def fee_list(request):
    search = request.GET.get('search', '').strip()
    month = request.GET.get('month', '').strip()
    status = request.GET.get('status', '').strip()

    payments = FeePayment.objects.select_related('student', 'student__route', 'student__van').all()

    if search:
        payments = payments.filter(
            Q(student__admission_number__icontains=search) |
            Q(student__name__icontains=search) |
            Q(challan__challan_number__icontains=search) |
            Q(voucher__voucher_number__icontains=search)
        )
    if month:
        payments = payments.filter(month__icontains=month)
    if status in ['Paid', 'Unpaid']:
        payments = payments.filter(status=status)

    all_months = FeePayment.objects.values_list('month', flat=True).distinct()

    context = {
        'payments': payments,
        'search': search,
        'selected_month': month,
        'selected_status': status,
        'all_months': all_months,
    }
    return render(request, 'finance/fee_list.html', context)


@accountant_required
def generate_dues_view(request):
    current_month_str = timezone.now().strftime("%b %Y")
    if request.method == 'POST':
        form = GenerateDuesForm(request.POST)
        if form.is_valid():
            target_month = form.cleaned_data['month'].strip()
            result = generate_monthly_dues(target_month)
            messages.success(
                request,
                f"Generated {result['created']} monthly dues for '{target_month}'. "
                f"({result['skipped']} students already had dues or no route assigned)."
            )
            return redirect('finance:fee_list')
    else:
        form = GenerateDuesForm(initial={'month': current_month_str})

    return render(request, 'finance/generate_dues.html', {'form': form})


@accountant_required
def generate_voucher_view(request, pk):
    payment = get_object_or_404(FeePayment, pk=pk)
    voucher = get_or_create_voucher(payment)
    return redirect('finance:print_voucher', pk=voucher.pk)


@accountant_required
def generate_challan_view(request, pk):
    payment = get_object_or_404(FeePayment, pk=pk)
    challan = get_or_create_challan(payment)
    return redirect('finance:print_challan', pk=challan.pk)


@accountant_required
def mark_paid_view(request, pk):
    payment = get_object_or_404(FeePayment, pk=pk)
    if payment.status == FeePayment.Status.PAID:
        messages.info(request, "This fee is already paid in full.")
        if hasattr(payment, 'receipt'):
            return redirect('finance:print_receipt', pk=payment.receipt.pk)
        return redirect('finance:fee_list')

    if request.method == 'POST':
        form = PaymentRecordForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount_paid']
            notes = form.cleaned_data['notes']
            receipt = record_payment(payment, amount, notes)
            messages.success(request, f"Payment recorded successfully! Receipt {receipt.receipt_number} generated.")
            return redirect('finance:print_receipt', pk=receipt.pk)
    else:
        form = PaymentRecordForm(initial={'amount_paid': payment.amount})

    return render(request, 'finance/mark_paid.html', {'form': form, 'payment': payment})


def print_voucher(request, pk):
    voucher = get_object_or_404(Voucher.objects.select_related('fee_payment__student__route', 'fee_payment__student__van'), pk=pk)
    return render(request, 'finance/print_voucher.html', {'voucher': voucher})


def print_challan(request, pk):
    challan = get_object_or_404(Challan.objects.select_related('fee_payment__student__route', 'fee_payment__student__van'), pk=pk)
    return render(request, 'finance/print_challan.html', {'challan': challan})


def print_receipt(request, pk):
    receipt = get_object_or_404(Receipt.objects.select_related('fee_payment__student__route', 'fee_payment__student__van'), pk=pk)
    return render(request, 'finance/print_receipt.html', {'receipt': receipt})
