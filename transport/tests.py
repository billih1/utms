from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from transport.models import Route, Van
from students.models import Student


class TransportAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('trans_admin', 'adm@t.com', 'pass123')
        self.admin.role = User.Role.ADMIN
        self.admin.save()
        self.client.force_login(self.admin)

        self.route = Route.objects.create(route_name='Peoples Colony', rent=Decimal('4500.00'), description='Via D-Ground')
        self.van = Van.objects.create(van_number='FDN-201', capacity=20, route=self.route)
        self.spare_van = Van.objects.create(van_number='SPARE-01', capacity=22, route=None)

    def test_model_properties_and_str(self):
        self.assertIn('Peoples Colony', str(self.route))
        self.assertIn('4,500', str(self.route))
        self.assertEqual(self.route.total_vans, 1)
        self.assertEqual(self.route.total_students, 0)

        self.assertIn('FDN-201', str(self.van))
        self.assertIn('Spare Vehicle', str(self.spare_van))
        self.assertEqual(self.van.filled_seats, 0)
        self.assertEqual(self.van.available_seats, 20)
        self.assertFalse(self.van.is_full)
        self.assertTrue(self.spare_van.is_spare)

    def test_route_views_crud(self):
        # Route list
        res = self.client.get(reverse('transport:route_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Peoples Colony')

        # Route create GET & POST
        res = self.client.get(reverse('transport:route_create'))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:route_create'), {
            'route_name': 'Madina Town',
            'rent': '5200.00',
            'description': 'Main Canal Road',
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Route.objects.filter(route_name='Madina Town').exists())

        # Route edit
        new_route = Route.objects.get(route_name='Madina Town')
        res = self.client.get(reverse('transport:route_edit', args=[new_route.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:route_edit', args=[new_route.id]), {
            'route_name': 'Madina Town Express',
            'rent': '5500.00',
            'description': 'Updated',
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        new_route.refresh_from_db()
        self.assertEqual(new_route.route_name, 'Madina Town Express')

        # Route delete
        res = self.client.get(reverse('transport:route_delete', args=[new_route.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:route_delete', args=[new_route.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Route.objects.filter(id=new_route.id).exists())

    def test_route_delete_blocked_when_students_assigned(self):
        Student.objects.create(
            admission_number='2024-TR-01',
            name='Route Stu',
            program='BSCS',
            semester='1st',
            route=self.route,
            van=self.van
        )
        res = self.client.post(reverse('transport:route_delete', args=[self.route.id]))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Route.objects.filter(id=self.route.id).exists())

    def test_van_views_crud(self):
        # Van list
        res = self.client.get(reverse('transport:van_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'FDN-201')

        # Van create GET & POST
        res = self.client.get(reverse('transport:van_create'))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:van_create'), {
            'van_number': 'FSD-999',
            'capacity': 22,
            'route': self.route.id,
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Van.objects.filter(van_number='FSD-999').exists())

        # Van edit
        new_van = Van.objects.get(van_number='FSD-999')
        res = self.client.get(reverse('transport:van_edit', args=[new_van.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:van_edit', args=[new_van.id]), {
            'van_number': 'FSD-999',
            'capacity': 21,
            'route': '',
            'is_active': True
        })
        self.assertEqual(res.status_code, 302)
        new_van.refresh_from_db()
        self.assertEqual(new_van.capacity, 21)
        self.assertIsNone(new_van.route)

        # Van delete
        res = self.client.get(reverse('transport:van_delete', args=[new_van.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('transport:van_delete', args=[new_van.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(Van.objects.filter(id=new_van.id).exists())

    def test_van_delete_blocked_when_students_assigned(self):
        Student.objects.create(
            admission_number='2024-VN-01',
            name='Van Stu',
            program='BSCS',
            semester='1st',
            route=self.route,
            van=self.van
        )
        res = self.client.post(reverse('transport:van_delete', args=[self.van.id]))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(Van.objects.filter(id=self.van.id).exists())
