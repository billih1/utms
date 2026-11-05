import os
import json
import uuid
import qrcode
from io import BytesIO
from decimal import Decimal
from django.core.files.base import ContentFile
from django.utils import timezone
from students.models import Student
from .models import FeePayment, Voucher, Challan, Receipt


def generate_monthly_dues(month_str: str) -> dict:
    """
    FR-10 / UC-08: Automatically create fee payment records for all active students
    assigned to a route for the given month.
    """
    students = Student.objects.filter(is_active=True, route__isnull=False).select_related('route')
    created_count = 0
    skipped_count = 0

    for s in students:
        rent = s.route.rent
        obj, created = FeePayment.objects.get_or_create(
            student=s,
            month=month_str,
            defaults={
                'amount': rent,
                'amount_paid': Decimal('0.00'),
                'status': FeePayment.Status.UNPAID,
            }
        )
        if created:
            created_count += 1
        else:
            skipped_count += 1

    return {
        'created': created_count,
        'skipped': skipped_count,
        'month': month_str,
    }


def build_qr_image_file(payload_dict: dict, prefix: str = 'doc') -> ContentFile:
    """Generates a QR code image as a Django ContentFile."""
    qr_json_str = json.dumps(payload_dict, indent=2)
    qr = qrcode.QRCode(
        version=1,
        box_size=6,
        border=2,
    )
    qr.add_data(qr_json_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
    return ContentFile(buffer.getvalue(), name=filename), qr_json_str


def get_or_create_voucher(fee_payment: FeePayment) -> Voucher:
    """UC-09: Generates fee voucher with verifiable QR code."""
    if hasattr(fee_payment, 'voucher'):
        return fee_payment.voucher

    payload = {
        'type': 'voucher',
        'doc_number': f"VCH-{uuid.uuid4().hex[:8].upper()}",
        'student': fee_payment.student.name,
        'admission': fee_payment.student.admission_number,
        'amount': float(fee_payment.amount),
        'month': fee_payment.month,
        'status': fee_payment.status,
        'generated_at': timezone.now().isoformat(),
    }
    content_file, qr_json = build_qr_image_file(payload, prefix='voucher')

    voucher = Voucher(
        fee_payment=fee_payment,
        voucher_number=payload['doc_number'],
        qr_data=qr_json
    )
    voucher.qr_image.save(content_file.name, content_file, save=False)
    voucher.save()
    return voucher


def get_or_create_challan(fee_payment: FeePayment) -> Challan:
    """UC-10: Generates unique 3-part bank challan with bank account transfer QR code."""
    if hasattr(fee_payment, 'challan'):
        challan = fee_payment.challan
        if not challan.qr_image:
            _attach_challan_qr(challan)
            challan.save()
        return challan

    challan_num = f"CHN-{uuid.uuid4().hex[:8].upper()}"
    challan = Challan(
        fee_payment=fee_payment,
        challan_number=challan_num,
        bank_name='National Bank of Pakistan (NBP)',
        branch_code='0451 - GCUF Main Campus',
        account_title='GCUF Transport Fee Collection Account',
        account_number='04510034829101',
        iban='PK36NBPA0004510034829101',
        raast_id='gcuf-transport@nbp',
    )
    _attach_challan_qr(challan)
    challan.save()
    return challan


def _attach_challan_qr(challan: Challan) -> None:
    fp = challan.fee_payment
    st = fp.student
    payload = {
        'type': 'GCUF_BANK_CHALLAN',
        'challan_no': challan.challan_number,
        'bank': challan.bank_name,
        'branch_code': challan.branch_code,
        'account_title': challan.account_title,
        'account_number': challan.account_number,
        'iban': challan.iban,
        'raast_id': challan.raast_id,
        'student': st.name,
        'admission_no': st.admission_number,
        'route': st.route.route_name if st.route else 'N/A',
        'van': st.van.van_number if st.van else 'N/A',
        'fee_month': fp.month,
        'amount_pkr': float(fp.amount),
        'raast_pay_uri': f"raast://pay?iban={challan.iban}&amount={fp.amount}&ref={challan.challan_number}",
        'issued_at': timezone.now().isoformat(),
    }
    content_file, qr_json = build_qr_image_file(payload, prefix='challan')
    challan.qr_data = qr_json
    challan.qr_image.save(content_file.name, content_file, save=False)


def record_payment(fee_payment: FeePayment, amount_paid: Decimal, notes: str = '') -> Receipt:
    """
    UC-11: Records payment and produces printable receipt with QR verification.
    """
    fee_payment.amount_paid = amount_paid
    if amount_paid >= fee_payment.amount:
        fee_payment.status = FeePayment.Status.PAID
    fee_payment.paid_at = timezone.now()
    if notes:
        fee_payment.notes = notes
    fee_payment.save()

    if hasattr(fee_payment, 'receipt'):
        receipt = fee_payment.receipt
    else:
        receipt_num = f"RCT-{uuid.uuid4().hex[:8].upper()}"
        payload = {
            'type': 'receipt',
            'doc_number': receipt_num,
            'student': fee_payment.student.name,
            'admission': fee_payment.student.admission_number,
            'amount_paid': float(amount_paid),
            'month': fee_payment.month,
            'status': fee_payment.status,
            'paid_at': fee_payment.paid_at.isoformat(),
        }
        content_file, _ = build_qr_image_file(payload, prefix='receipt')

        receipt = Receipt(fee_payment=fee_payment, receipt_number=receipt_num)
        receipt.qr_image.save(content_file.name, content_file, save=False)
        receipt.save()

    return receipt
