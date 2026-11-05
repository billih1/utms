import io
import openpyxl
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student
from finance.models import FeePayment


class ReportsAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.accountant = User.objects.create_user('rep_acc', 'acc@t.com', 'pass123')
        self.accountant.role = User.Role.ACCOUNTANT
        self.accountant.save()
        self.client.force_login(self.accountant)

        self.route = Route.objects.create(route_name='Millat Town', rent=Decimal('4800.00'))
        self.van = Van.objects.create(van_number='MLT-01', capacity=22, route=self.route)

        self.student = Student.objects.create(
            admission_number='2024-REP-001',
            name='Report Student',
            program='BSIT',
            semester='4th',
            route=self.route,
            van=self.van,
            is_active=True
        )

        # Create paid payment and unpaid payment
        FeePayment.objects.create(
            student=self.student,
            month='Sep 2026',
            amount=Decimal('4800.00'),
            amount_paid=Decimal('4800.00'),
            status=FeePayment.Status.PAID
        )
        FeePayment.objects.create(
            student=self.student,
            month='Oct 2026',
            amount=Decimal('4800.00'),
            amount_paid=Decimal('0.00'),
            status=FeePayment.Status.UNPAID
        )

    def test_monthly_collection_report_view(self):
        # Default month
        res = self.client.get(reverse('reports:monthly_collection'))
        self.assertEqual(res.status_code, 200)

        # Specific month
        res = self.client.get(reverse('reports:monthly_collection'), {'month': 'Sep 2026'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Millat Town')
        self.assertContains(res, '4800')

    def test_due_remaining_report_view(self):
        res = self.client.get(reverse('reports:due_remaining'), {'month': 'Oct 2026'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Report Student')
        self.assertContains(res, '4800')

    def test_defaulter_report_view(self):
        res = self.client.get(reverse('reports:defaulter_report'), {'month': 'Oct 2026'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Report Student')
        self.assertContains(res, '4800')

    def test_export_excel_defaulters(self):
        res = self.client.get(reverse('reports:export_excel'), {'type': 'defaulters', 'month': 'Oct 2026'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('TMS_defaulters_Oct_2026.xlsx', res['Content-Disposition'])

        # Read back excel
        wb = openpyxl.load_workbook(io.BytesIO(res.content))
        ws = wb.active
        self.assertEqual(ws.cell(row=1, column=1).value, 'Adm No')
        self.assertEqual(ws.cell(row=2, column=1).value, '2024-REP-001')

    def test_export_excel_collection(self):
        res = self.client.get(reverse('reports:export_excel'), {'type': 'collection', 'month': 'Sep 2026'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertIn('TMS_collection_Sep_2026.xlsx', res['Content-Disposition'])

        wb = openpyxl.load_workbook(io.BytesIO(res.content))
        ws = wb.active
        self.assertEqual(ws.cell(row=1, column=1).value, 'Route Name')
        self.assertEqual(ws.cell(row=2, column=1).value, 'Millat Town')
