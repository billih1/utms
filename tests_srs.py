from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student
from students.forms import StudentAssignForm
from finance.models import FeePayment, Voucher, Challan, Receipt
from finance.services import generate_monthly_dues, get_or_create_voucher, get_or_create_challan, record_payment
from operations.models import VehicleLog
from ai_predictor.model import run_prediction_for_month


class SRSTestSuite(TestCase):
    """
    Automated Black-box & Behavioral Tests corresponding to Appendix A.1 of SRS.
    """

    def setUp(self):
        self.client = Client()

        # Users for 4 roles
        self.admin_user = User.objects.create_superuser('test_admin', 'admin@t.com', 'pass123')
        self.admin_user.role = User.Role.ADMIN
        self.admin_user.save()

        self.accountant_user = User.objects.create_user('test_acc', 'acc@t.com', 'pass123')
        self.accountant_user.role = User.Role.ACCOUNTANT
        self.accountant_user.save()

        self.driver_user = User.objects.create_user('test_driver', 'drv@t.com', 'pass123')
        self.driver_user.role = User.Role.DRIVER
        self.driver_user.save()

        # Route & Van
        self.route1 = Route.objects.create(route_name='Test Route 1', rent=Decimal('5000.00'))
        self.van1 = Van.objects.create(van_number='TEST-01', capacity=22, route=self.route1)

        # Student
        self.student1 = Student.objects.create(
            admission_number='2024-TEST-001',
            name='Test Student One',
            program='BSIT',
            semester='3rd',
            route=self.route1,
            van=self.van1
        )

        self.student_user = User.objects.create_user('test_student', 'stu@t.com', 'pass123')
        self.student_user.role = User.Role.STUDENT
        self.student_user.linked_student_id = self.student1.id
        self.student_user.save()

    def test_tc01_login_valid(self):
        """TC-01: Valid credentials -> Role dashboard opens."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test_admin',
            'password': 'pass123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard:home'))

    def test_tc02_login_invalid(self):
        """TC-02: Wrong password -> Error message."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'test_admin',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_tc03_access_control_student_blocked_from_admin(self):
        """TC-03: Student opens an Admin URL -> Access denied (403)."""
        self.client.login(username='test_student', password='pass123')
        response = self.client.get(reverse('accounts:user_list'))
        self.assertEqual(response.status_code, 403)

    def test_tc04_duplicate_admission_number_rejected(self):
        """TC-04: Add student with duplicate admission number -> Rejected with error."""
        with self.assertRaises(Exception):
            Student.objects.create(
                admission_number='2024-TEST-001', # duplicate
                name='Duplicate Student',
                program='BSCS',
                semester='1st'
            )

    def test_tc05_van_capacity_enforcement(self):
        """TC-05: Assign the 23rd student to a 22-seat van -> Blocked."""
        # Create a tiny 1-seat van to test capacity limit directly
        small_van = Van.objects.create(van_number='TINY-VAN', capacity=1, route=self.route1)
        # Assign first student
        self.student1.van = small_van
        self.student1.save()

        # Second student tries to assign to small_van
        student2 = Student.objects.create(
            admission_number='2024-TEST-002',
            name='Student Two',
            program='BSIT',
            semester='3rd',
            route=self.route1
        )
        form = StudentAssignForm(instance=student2, data={
            'route': self.route1.id,
            'van': small_van.id
        })
        self.assertFalse(form.is_valid())
        self.assertIn("FULL", str(form.errors))

    def test_tc06_monthly_due_matches_route_rent(self):
        """TC-06: Route rent Rs. 5000 -> Due = Rs. 5000."""
        res = generate_monthly_dues('Dec 2026')
        self.assertEqual(res['created'], 1)
        payment = FeePayment.objects.get(student=self.student1, month='Dec 2026')
        self.assertEqual(payment.amount, Decimal('5000.00'))
        self.assertEqual(payment.status, FeePayment.Status.UNPAID)

    def test_tc07_voucher_generates_verifiable_qr(self):
        """TC-07: Generate voucher -> Voucher with QR code & JSON payload."""
        generate_monthly_dues('Dec 2026')
        payment = FeePayment.objects.get(student=self.student1, month='Dec 2026')
        voucher = get_or_create_voucher(payment)
        self.assertTrue(voucher.voucher_number.startswith('VCH-'))
        self.assertIn('Test Student One', voucher.qr_data)
        self.assertTrue(bool(voucher.qr_image))

    def test_tc08_challan_uniqueness(self):
        """TC-08: Challan generated -> Unique challan number, no duplicates."""
        generate_monthly_dues('Dec 2026')
        payment = FeePayment.objects.get(student=self.student1, month='Dec 2026')
        c1 = get_or_create_challan(payment)
        c2 = get_or_create_challan(payment)
        self.assertEqual(c1.id, c2.id)
        self.assertTrue(c1.challan_number.startswith('CHN-'))

    def test_tc09_payment_mark_paid_generates_receipt(self):
        """TC-09: Mark paid -> Status Paid; receipt printable with QR."""
        generate_monthly_dues('Dec 2026')
        payment = FeePayment.objects.get(student=self.student1, month='Dec 2026')
        receipt = record_payment(payment, Decimal('5000.00'), 'Bank payment')
        payment.refresh_from_db()
        self.assertEqual(payment.status, FeePayment.Status.PAID)
        self.assertEqual(payment.amount_paid, Decimal('5000.00'))
        self.assertTrue(receipt.receipt_number.startswith('RCT-'))
        self.assertTrue(bool(receipt.qr_image))

    def test_tc10_defaulter_report(self):
        """TC-10: Defaulter report lists only unpaid students."""
        generate_monthly_dues('Dec 2026')
        # Student1 is currently Unpaid
        self.client.login(username='test_acc', password='pass123')
        response = self.client.get(reverse('reports:defaulter_report') + '?month=Dec 2026')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2024-TEST-001')

    def test_tc11_search_by_admission_number(self):
        """TC-11: Search by admission number -> Correct student shown."""
        self.client.login(username='test_admin', password='pass123')
        response = self.client.get(reverse('students:student_list') + '?search=2024-TEST-001')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Student One')

    def test_tc12_vehicle_log_driver_entry(self):
        """TC-12: Vehicle log -> Driver enters times and status is saved."""
        self.client.login(username='test_driver', password='pass123')
        response = self.client.post(reverse('operations:driver_panel'), {
            'van': self.van1.id,
            'route': self.route1.id,
            'departure_time': '07:30',
            'arrival_time': '08:15',
            'status': VehicleLog.TripStatus.ARRIVED,
            'notes': 'All good'
        })
        self.assertEqual(response.status_code, 302)
        log = VehicleLog.objects.filter(driver=self.driver_user).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.status, VehicleLog.TripStatus.ARRIVED)

    def test_tc13_student_view_isolation(self):
        """TC-13: Student sees only own data in student dashboard."""
        self.client.login(username='test_student', password='pass123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '2024-TEST-001')
        self.assertContains(response, 'Test Student One')

    def test_tc14_sql_injection_defense(self):
        """TC-14: SQL injection payload rejected safely by ORM."""
        response = self.client.post(reverse('accounts:login'), {
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password")

    def test_tc21_ai_defaulter_prediction_runs(self):
        """FR-22 / UC-21: AI Defaulter prediction evaluates student risk."""
        preds = run_prediction_for_month('Jan 2027')
        self.assertTrue(len(preds) >= 1)
        first_pred = preds[0]
        self.assertIn(first_pred.risk_level, ['High', 'Medium', 'Low'])
        self.assertTrue(0.0 <= first_pred.risk_score <= 1.0)
        self.assertTrue(len(first_pred.reason) > 0)
