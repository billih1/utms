from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from transport.models import Route, Van
from operations.models import VehicleLog


class OperationsAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create_superuser('op_admin', 'adm@t.com', 'pass123')
        self.admin.role = User.Role.ADMIN
        self.admin.save()

        self.driver = User.objects.create_user('op_driver', 'drv@t.com', 'pass123')
        self.driver.role = User.Role.DRIVER
        self.driver.save()

        self.route = Route.objects.create(route_name='Satiana Road', rent=3800)
        self.van = Van.objects.create(van_number='STR-01', capacity=22, route=self.route)

    def test_vehicle_log_model_str(self):
        log = VehicleLog.objects.create(
            van=self.van,
            route=self.route,
            driver=self.driver,
            status=VehicleLog.TripStatus.SCHEDULED
        )
        self.assertIn('STR-01', str(log))
        self.assertIn('Scheduled', str(log))

    def test_driver_panel_flow(self):
        self.client.force_login(self.driver)

        # GET driver panel
        res = self.client.get(reverse('operations:driver_panel'))
        self.assertEqual(res.status_code, 200)

        # POST trip update
        res = self.client.post(reverse('operations:driver_panel'), {
            'van': self.van.id,
            'route': self.route.id,
            'departure_time': '07:30',
            'arrival_time': '08:15',
            'status': 'Arrived',
            'notes': 'Normal transit'
        })
        self.assertEqual(res.status_code, 302)

        log = VehicleLog.objects.filter(driver=self.driver).latest('created_at')
        self.assertEqual(log.status, 'Arrived')
        self.assertEqual(log.van, self.van)
        self.assertEqual(log.driver, self.driver)

    def test_driver_panel_access_denied_for_students(self):
        student_user = User.objects.create_user('op_stu', 'stu@t.com', 'pass123', role='Student')
        self.client.force_login(student_user)
        res = self.client.get(reverse('operations:driver_panel'))
        self.assertEqual(res.status_code, 403)

    def test_admin_vehicle_log_list_and_filter(self):
        VehicleLog.objects.create(
            van=self.van,
            route=self.route,
            driver=self.driver,
            status=VehicleLog.TripStatus.DEPARTED,
            date=timezone.now().date()
        )

        self.client.force_login(self.admin)
        res = self.client.get(reverse('operations:vehicle_log_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'STR-01')

        # Filter by van
        res = self.client.get(reverse('operations:vehicle_log_list'), {'van': self.van.id})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'STR-01')

        # Filter by date
        today_str = timezone.now().date().isoformat()
        res = self.client.get(reverse('operations:vehicle_log_list'), {'date': today_str})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'STR-01')
