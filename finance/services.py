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
    """UC-10: Generates unique challan slip."""
    if hasattr(fee_payment, 'challan'):
        return fee_payment.challan

    challan = Challan.objects.create(fee_payment=fee_payment)
    return challan


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
