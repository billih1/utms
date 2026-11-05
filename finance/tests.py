from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student
from finance.models import FeePayment, Voucher, Challan, Receipt
from finance.services import generate_monthly_dues, get_or_create_voucher, get_or_create_challan, record_payment


class FinanceAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.accountant = User.objects.create_user('fin_acc', 'fin@t.com', 'pass123')
        self.accountant.role = User.Role.ACCOUNTANT
        self.accountant.save()
        self.client.force_login(self.accountant)

        self.route = Route.objects.create(route_name='Jhang Road', rent=Decimal('4200.00'))
        self.van = Van.objects.create(van_number='JH-01', capacity=20, route=self.route)
        self.student = Student.objects.create(
            admission_number='2024-FIN-001',
            name='Fin Student',
            program='BSSE',
            semester='4th',
            route=self.route,
            van=self.van,
            is_active=True
        )

    def test_generate_monthly_dues_and_batch_skip(self):
        # 1st batch generation -> created 1
        res = generate_monthly_dues('Oct 2026')
        self.assertEqual(res['created'], 1)
        self.assertEqual(res['skipped'], 0)

        # Verify payment created
        p = FeePayment.objects.get(student=self.student, month='Oct 2026')
        self.assertEqual(p.amount, Decimal('4200.00'))
        self.assertEqual(p.status, FeePayment.Status.UNPAID)
        self.assertIn('2024-FIN-001', str(p))

        # 2nd batch generation for same month -> skipped 1
        res2 = generate_monthly_dues('Oct 2026')
        self.assertEqual(res2['created'], 0)
        self.assertEqual(res2['skipped'], 1)

    def test_fee_list_view_and_filtering(self):
        generate_monthly_dues('Nov 2026')
        res = self.client.get(reverse('finance:fee_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '2024-FIN-001')

        # Filter by search
        res = self.client.get(reverse('finance:fee_list'), {'search': '2024-FIN-001'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Fin Student')

        # Filter by month and status
        res = self.client.get(reverse('finance:fee_list'), {'month': 'Nov 2026', 'status': 'Unpaid'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Fin Student')

    def test_voucher_and_qr_generation(self):
        generate_monthly_dues('Dec 2026')
        payment = FeePayment.objects.get(student=self.student, month='Dec 2026')

        # Trigger voucher view
        res = self.client.get(reverse('finance:generate_voucher', args=[payment.id]))
        self.assertEqual(res.status_code, 302)

        voucher = Voucher.objects.get(fee_payment=payment)
        self.assertIn('VCH-', voucher.voucher_number)
        self.assertIn('2024-FIN-001', voucher.qr_data)
        self.assertTrue(bool(voucher.qr_image))
        self.assertIn(voucher.voucher_number, str(voucher))

        # Print voucher view
        res = self.client.get(reverse('finance:print_voucher', args=[voucher.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, voucher.voucher_number)

    def test_challan_generation_and_print(self):
        generate_monthly_dues('Jan 2027')
        payment = FeePayment.objects.get(student=self.student, month='Jan 2027')

        # Trigger challan view
        res = self.client.get(reverse('finance:generate_challan', args=[payment.id]))
        self.assertEqual(res.status_code, 302)

        challan = Challan.objects.get(fee_payment=payment)
        self.assertIn('CHN-', challan.challan_number)
        self.assertIn(challan.challan_number, str(challan))

        # Print challan view (renders 3-part bank slip)
        res = self.client.get(reverse('finance:print_challan', args=[challan.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Bank Copy')
        self.assertContains(res, 'Accounts Copy')
        self.assertContains(res, 'Student Copy')

    def test_payment_recording_and_receipt(self):
        generate_monthly_dues('Feb 2027')
        payment = FeePayment.objects.get(student=self.student, month='Feb 2027')

        # GET mark paid
        res = self.client.get(reverse('finance:mark_paid', args=[payment.id]))
        self.assertEqual(res.status_code, 200)

        # POST mark paid full amount
        res = self.client.post(reverse('finance:mark_paid', args=[payment.id]), {
            'amount_paid': '4200.00',
            'notes': 'Paid at NBP Bank Booth'
        })
        self.assertEqual(res.status_code, 302)

        payment.refresh_from_db()
        self.assertEqual(payment.status, FeePayment.Status.PAID)
        self.assertEqual(payment.amount_paid, Decimal('4200.00'))

        receipt = Receipt.objects.get(fee_payment=payment)
        self.assertIn('RCT-', receipt.receipt_number)
        self.assertIn(receipt.receipt_number, str(receipt))

        # Print receipt view
        res = self.client.get(reverse('finance:print_receipt', args=[receipt.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, receipt.receipt_number)

        # Re-visiting mark paid for already paid fee redirects to receipt
        res = self.client.get(reverse('finance:mark_paid', args=[payment.id]))
        self.assertEqual(res.status_code, 302)

    def test_partial_payment_recording(self):
        generate_monthly_dues('Mar 2027')
        payment = FeePayment.objects.get(student=self.student, month='Mar 2027')

        # Pay less than full amount
        record_payment(payment, Decimal('2000.00'), 'Partial deposit')
        payment.refresh_from_db()
        self.assertEqual(payment.status, FeePayment.Status.UNPAID)
        self.assertEqual(payment.amount_paid, Decimal('2000.00'))

    def test_challan_bank_qr_and_account_details(self):
        generate_monthly_dues('Apr 2027')
        payment = FeePayment.objects.get(student=self.student, month='Apr 2027')
        challan = get_or_create_challan(payment)

        self.assertEqual(challan.bank_name, 'National Bank of Pakistan (NBP)')
        self.assertEqual(challan.account_number, '04510034829101')
        self.assertEqual(challan.iban, 'PK36NBPA0004510034829101')
        self.assertTrue(bool(challan.qr_image))
        self.assertIn('raast://pay', challan.qr_data)
        self.assertIn('04510034829101', challan.qr_data)

    def test_bulk_print_challans_and_vouchers(self):
        generate_monthly_dues('May 2027')

        # Bulk challans view
        res = self.client.get(reverse('finance:bulk_print_challans'), {'month': 'May 2027'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'NATIONAL BANK OF PAKISTAN')
        self.assertContains(res, 'Bank Copy')
        self.assertContains(res, 'Accounts Copy')
        self.assertContains(res, 'Student Copy')

        # Bulk vouchers view
        res = self.client.get(reverse('finance:bulk_print_vouchers'), {'month': 'May 2027'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Fee Vouchers Batch')

    def test_print_receipt_with_remaining_dues_ledger(self):
        # Create an unpaid prior month
        FeePayment.objects.create(
            student=self.student,
            month='Jan 2026',
            amount=Decimal('4200.00'),
            amount_paid=Decimal('0.00'),
            status=FeePayment.Status.UNPAID
        )
        # Create paid current month
        curr = FeePayment.objects.create(
            student=self.student,
            month='Feb 2026',
            amount=Decimal('4200.00'),
            amount_paid=Decimal('4200.00'),
            status=FeePayment.Status.PAID
        )
        receipt = record_payment(curr, Decimal('4200.00'), 'Paid via Bank')

        res = self.client.get(reverse('finance:print_receipt', args=[receipt.pk]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Transport Account Ledger')
        self.assertContains(res, 'Total Remaining Dues')
        self.assertContains(res, '4200')
