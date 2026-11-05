from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student


class StudentAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('stu_admin', 'stuadm@t.com', 'pass123')
        self.admin.role = User.Role.ADMIN
        self.admin.save()
        self.client.force_login(self.admin)

        self.route = Route.objects.create(route_name='Samundri Road', rent=Decimal('4000.00'))
        self.van = Van.objects.create(van_number='SR-101', capacity=2, route=self.route)
        self.student = Student.objects.create(
            admission_number='2024-STU-001',
            name='Ali Raza',
            program='BSIT',
            semester='5th',
            phone='03001234567',
            route=self.route,
            van=self.van,
            is_active=True
        )

    def test_student_model_str(self):
        self.assertEqual(str(self.student), '2024-STU-001 - Ali Raza')

    def test_student_list_and_filters(self):
        # Base list
        res = self.client.get(reverse('students:student_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ali Raza')

        # Filter by search
        res = self.client.get(reverse('students:student_list'), {'search': '2024-STU-001'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ali Raza')

        # Filter by program and semester
        res = self.client.get(reverse('students:student_list'), {'program': 'BSIT', 'semester': '5th'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ali Raza')

        # Filter by route and van
        res = self.client.get(reverse('students:student_list'), {'route': self.route.id, 'van': self.van.id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ali Raza')

        # Filter by status
        res = self.client.get(reverse('students:student_list'), {'status': 'active'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Ali Raza')

        res = self.client.get(reverse('students:student_list'), {'status': 'inactive'})
        self.assertEqual(res.status_code, 200)
        self.assertNotContains(res, 'Ali Raza')

    def test_student_create_and_detail(self):
        res = self.client.get(reverse('students:student_create'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('students:student_create'), {
            'admission_number': '2024-STU-002',
            'name': 'Hamza Khan',
            'program': 'BSCS',
            'semester': '1st',
            'phone': '03007654321',
            'route': self.route.id,
            'van': self.van.id,
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        new_stu = Student.objects.get(admission_number='2024-STU-002')

        # Detail view
        res = self.client.get(reverse('students:student_detail', args=[new_stu.id]))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Hamza Khan')

    def test_student_edit_and_delete(self):
        # Edit
        res = self.client.get(reverse('students:student_edit', args=[self.student.id]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('students:student_edit', args=[self.student.id]), {
            'admission_number': '2024-STU-001',
            'name': 'Ali Raza Updated',
            'program': 'BSIT',
            'semester': '6th',
            'phone': '03009999999',
            'route': self.route.id,
            'van': self.van.id,
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        self.student.refresh_from_db()
        self.assertEqual(self.student.name, 'Ali Raza Updated')
        self.assertEqual(self.student.semester, '6th')

        # Delete
        res = self.client.get(reverse('students:student_delete', args=[self.student.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('students:student_delete', args=[self.student.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Student.objects.filter(id=self.student.id).exists())

    def test_student_assign_and_overfill_blocking(self):
        # Van capacity is 2
        # Create student 2 and assign to van -> capacity reached (2/2)
        s2 = Student.objects.create(
            admission_number='2024-STU-003',
            name='Seat Two',
            program='BSCS',
            semester='2nd',
            route=self.route,
            van=self.van
        )
        self.assertTrue(self.van.is_full)

        # Create student 3 without van
        s3 = Student.objects.create(
            admission_number='2024-STU-004',
            name='Seat Three Overflow',
            program='BSCS',
            semester='2nd',
            route=self.route
        )

        # Attempt to assign s3 to self.van -> must be rejected
        res = self.client.post(reverse('students:student_assign', args=[s3.id]), {
            'route': self.route.id,
            'van': self.van.id
        })
        self.assertEqual(res.status_code, 200) # Form re-rendered with error
        self.assertContains(res, 'is full')

        # Student remains unassigned to van
        s3.refresh_from_db()
        self.assertIsNone(s3.van)

    def test_get_vans_for_route_htmx(self):
        res = self.client.get(reverse('students:get_vans_for_route', args=[self.route.id]))
        self.assertEqual(res.status_code, 200)
        self.assertIn('SR-101', res.content.decode('utf-8'))
