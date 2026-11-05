from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum
from decimal import Decimal
from django.utils import timezone
from accounts.decorators import accountant_required
from students.models import Student
from transport.models import Route
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
    # Ensure QR code is attached if missing
    if not challan.qr_image:
        challan = get_or_create_challan(challan.fee_payment)
    return render(request, 'finance/print_challan.html', {'challan': challan})


@accountant_required
def bulk_print_challans(request):
    """
    Bulk print 3-part bank deposit challans for all students for a selected month and optional route.
    Each student's 3-part challan is formatted to print on its own landscape A4 page.
    """
    month = request.GET.get('month', '').strip()
    route_id = request.GET.get('route', '').strip()

    if not month:
        month = timezone.now().strftime("%b %Y")

    payments = FeePayment.objects.filter(month=month).select_related('student', 'student__route', 'student__van')
    if route_id:
        payments = payments.filter(student__route_id=route_id)

    challans = []
    for p in payments:
        challan = get_or_create_challan(p)
        challans.append(challan)

    routes = Route.objects.filter(is_active=True)

    return render(request, 'finance/bulk_print_challans.html', {
        'challans': challans,
        'selected_month': month,
        'selected_route': route_id,
        'routes': routes,
        'total_count': len(challans),
    })


@accountant_required
def bulk_print_vouchers(request):
    """
    Bulk print vouchers for all students for a selected month and optional route.
    """
    month = request.GET.get('month', '').strip()
    route_id = request.GET.get('route', '').strip()

    if not month:
        month = timezone.now().strftime("%b %Y")

    payments = FeePayment.objects.filter(month=month).select_related('student', 'student__route', 'student__van')
    if route_id:
        payments = payments.filter(student__route_id=route_id)

    vouchers = []
    for p in payments:
        voucher = get_or_create_voucher(p)
        vouchers.append(voucher)

    routes = Route.objects.filter(is_active=True)

    return render(request, 'finance/bulk_print_vouchers.html', {
        'vouchers': vouchers,
        'selected_month': month,
        'selected_route': route_id,
        'routes': routes,
        'total_count': len(vouchers),
    })


def print_receipt(request, pk):
    """
    Prints official fee payment receipt and student statement of account showing
    current payment settlement plus remaining dues breakdown across past and current months.
    """
    receipt = get_object_or_404(
        Receipt.objects.select_related(
            'fee_payment__student',
            'fee_payment__student__route',
            'fee_payment__student__van'
        ),
        pk=pk
    )
    student = receipt.fee_payment.student

    # All student fee history
    student_payments = FeePayment.objects.filter(student=student).order_by('-created_at', '-id')
    unpaid_payments = student_payments.filter(status=FeePayment.Status.UNPAID)
    total_remaining = unpaid_payments.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
    total_cleared = student_payments.filter(status=FeePayment.Status.PAID).aggregate(s=Sum('amount_paid'))['s'] or Decimal('0.00')

    # Latest unpaid challan if any remaining dues exist
    latest_unpaid_challan = None
    if unpaid_payments.exists():
        first_unpaid = unpaid_payments.first()
        latest_unpaid_challan = get_or_create_challan(first_unpaid)

    context = {
        'receipt': receipt,
        'student': student,
        'student_payments': student_payments,
        'unpaid_payments': unpaid_payments,
        'total_remaining': total_remaining,
        'total_cleared': total_cleared,
        'latest_unpaid_challan': latest_unpaid_challan,
    }
    return render(request, 'finance/print_receipt.html', context)
