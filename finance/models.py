import uuid
from django.db import models


class FeePayment(models.Model):
    """
    Monthly fee record for an enrolled student.
    GAP 7 RESOLUTION: stores amount, amount_paid, status, paid_at, notes.
    """
    class Status(models.TextChoices):
        PAID = 'Paid', 'Paid'
        UNPAID = 'Unpaid', 'Unpaid'

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fee_payments'
    )
    month = models.CharField(max_length=20, help_text="e.g., Nov 2026", db_index=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Full route rent dues")
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UNPAID)
    due_date = models.DateField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'month']

    def __str__(self):
        return f"{self.student.admission_number} - {self.month} ({self.status})"

    @property
    def remaining_amount(self):
        return max(0, self.amount - self.amount_paid)

    @property
    def has_voucher(self):
        return hasattr(self, 'voucher')

    @property
    def has_challan(self):
        return hasattr(self, 'challan')

    @property
    def has_receipt(self):
        return hasattr(self, 'receipt')


class Voucher(models.Model):
    """Fee voucher issued to the student, embedding a verifiable QR code."""
    fee_payment = models.OneToOneField(FeePayment, on_delete=models.CASCADE, related_name='voucher')
    voucher_number = models.CharField(max_length=50, unique=True, db_index=True)
    qr_data = models.TextField(help_text="Verifiable JSON payload encoded in QR")
    qr_image = models.ImageField(upload_to='qrcodes/vouchers/', blank=True, null=True)
    issue_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.voucher_number

    def save(self, *args, **kwargs):
        if not self.voucher_number:
            self.voucher_number = f"VCH-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Challan(models.Model):
    """Bank / Office payment deposit slip with unique tracking reference."""
    fee_payment = models.OneToOneField(FeePayment, on_delete=models.CASCADE, related_name='challan')
    challan_number = models.CharField(max_length=50, unique=True, db_index=True)
    bank_office_ref = models.CharField(max_length=100, blank=True, default='Accounts GCUF')
    issue_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.challan_number

    def save(self, *args, **kwargs):
        if not self.challan_number:
            self.challan_number = f"CHN-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Receipt(models.Model):
    """Receipt printed after successful fee settlement."""
    fee_payment = models.OneToOneField(FeePayment, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.CharField(max_length=50, unique=True, db_index=True)
    printed_at = models.DateTimeField(auto_now_add=True)
    qr_image = models.ImageField(upload_to='qrcodes/receipts/', blank=True, null=True)

    def __str__(self):
        return self.receipt_number

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            self.receipt_number = f"RCT-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)
