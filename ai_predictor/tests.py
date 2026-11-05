from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student
from finance.models import FeePayment
from ai_predictor.models import Prediction
from ai_predictor.features import extract_semester_number, extract_student_features
from ai_predictor.model import train_defaulter_model, run_prediction_for_month


class AIPredictorAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.accountant = User.objects.create_user('ai_acc', 'ai@t.com', 'pass123')
        self.accountant.role = User.Role.ACCOUNTANT
        self.accountant.save()
        self.client.force_login(self.accountant)

        self.route = Route.objects.create(route_name='D-Type Colony', rent=Decimal('4600.00'))
        self.van = Van.objects.create(van_number='DTC-01', capacity=22, route=self.route)

        self.student1 = Student.objects.create(
            admission_number='2024-AI-001',
            name='AI Student Clean',
            program='BSCS',
            semester='3rd',
            route=self.route,
            van=self.van,
            is_active=True
        )

        self.student2 = Student.objects.create(
            admission_number='2024-AI-002',
            name='AI Student Defaulter',
            program='BSIT',
            semester='7th',
            route=self.route,
            van=self.van,
            is_active=True
        )

        # Historical payments for Student 1 (all paid)
        FeePayment.objects.create(student=self.student1, month='Jan 2026', amount=4600, amount_paid=4600, status='Paid')
        FeePayment.objects.create(student=self.student1, month='Feb 2026', amount=4600, amount_paid=4600, status='Paid')

        # Historical payments for Student 2 (consecutive unpaid)
        FeePayment.objects.create(student=self.student2, month='Jan 2026', amount=4600, amount_paid=4600, status='Paid')
        FeePayment.objects.create(student=self.student2, month='Feb 2026', amount=4600, amount_paid=0, status='Unpaid')
        FeePayment.objects.create(student=self.student2, month='Mar 2026', amount=4600, amount_paid=0, status='Unpaid')

    def test_semester_parsing(self):
        self.assertEqual(extract_semester_number('1st'), 1)
        self.assertEqual(extract_semester_number('Semester 5'), 5)
        self.assertEqual(extract_semester_number(''), 1)
        self.assertEqual(extract_semester_number('Final'), 1)

    def test_feature_extraction(self):
        feat1 = extract_student_features(self.student1)
        self.assertEqual(feat1['total_months'], 2)
        self.assertEqual(feat1['paid_months'], 2)
        self.assertEqual(feat1['unpaid_months'], 0)
        self.assertEqual(feat1['payment_ratio'], 1.0)
        self.assertEqual(feat1['consecutive_defaults'], 0)

        feat2 = extract_student_features(self.student2)
        self.assertEqual(feat2['total_months'], 3)
        self.assertEqual(feat2['paid_months'], 1)
        self.assertEqual(feat2['unpaid_months'], 2)
        self.assertEqual(feat2['consecutive_defaults'], 2)
        self.assertAlmostEqual(feat2['payment_ratio'], 0.33, places=2)

    def test_run_prediction_for_month_and_model_representation(self):
        results = run_prediction_for_month('Apr 2026')
        self.assertEqual(len(results), 2)

        # Defaulter student should have High risk
        pred2 = Prediction.objects.get(student=self.student2, target_month='Apr 2026')
        self.assertEqual(pred2.risk_level, Prediction.RiskLevel.HIGH)
        self.assertGreaterEqual(pred2.risk_score, 0.70)
        self.assertIn('consecutive unpaid', pred2.reason)
        self.assertIn('2024-AI-002', str(pred2))

        # Clean student should have Low risk
        pred1 = Prediction.objects.get(student=self.student1, target_month='Apr 2026')
        self.assertEqual(pred1.risk_level, Prediction.RiskLevel.LOW)
        self.assertLess(pred1.risk_score, 0.40)
        self.assertIn('Consistent timely payment', pred1.reason)

    def test_ai_insights_view_get_and_post(self):
        # GET insights view
        res = self.client.get(reverse('ai_predictor:insights'))
        self.assertEqual(res.status_code, 200)

        # POST action='train'
        res = self.client.post(reverse('ai_predictor:insights'), {
            'action': 'train',
            'target_month': 'May 2026'
        })
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'May 2026')

    def test_access_denied_for_students(self):
        student_user = User.objects.create_user('ai_stu_user', 'stu@t.com', 'pass123', role='Student')
        self.client.force_login(student_user)
        res = self.client.get(reverse('ai_predictor:insights'))
        self.assertEqual(res.status_code, 403)
