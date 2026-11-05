from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from students.models import Student
from transport.models import Route, Van


class AccountsAppTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.admin = User.objects.create_superuser('acc_admin', 'adm@t.com', 'pass123')
        self.admin.role = User.Role.ADMIN
        self.admin.save()

        self.accountant = User.objects.create_user('acc_accountant', 'acc@t.com', 'pass123')
        self.accountant.role = User.Role.ACCOUNTANT
        self.accountant.save()

        self.driver = User.objects.create_user('acc_driver', 'drv@t.com', 'pass123')
        self.driver.role = User.Role.DRIVER
        self.driver.save()

        self.route = Route.objects.create(route_name='Sargodha Road', rent=4000)
        self.van = Van.objects.create(van_number='SGR-01', capacity=22, route=self.route)
        self.student_obj = Student.objects.create(
            admission_number='2024-ACC-001',
            name='Test Accounts Stu',
            program='BSCS',
            semester='3rd',
            route=self.route,
            van=self.van
        )

        self.student_user = User.objects.create_user('acc_student', 'stu@t.com', 'pass123')
        self.student_user.role = User.Role.STUDENT
        self.student_user.linked_student_id = self.student_obj.id
        self.student_user.save()

    def test_user_model_properties_and_str(self):
        self.assertEqual(str(self.admin), 'acc_admin (Admin)')
        self.assertTrue(self.admin.is_admin_role)
        self.assertTrue(self.admin.is_accountant)
        self.assertFalse(self.admin.is_driver)
        self.assertFalse(self.admin.is_student_role)

        self.assertFalse(self.accountant.is_admin_role)
        self.assertTrue(self.accountant.is_accountant)

        self.assertTrue(self.driver.is_driver)
        self.assertTrue(self.student_user.is_student_role)

    def test_login_logout_flow(self):
        # GET login
        res = self.client.get(reverse('accounts:login'))
        self.assertEqual(res.status_code, 200)

        # POST valid
        res = self.client.post(reverse('accounts:login'), {'username': 'acc_admin', 'password': 'pass123'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('dashboard:home'))

        # When authenticated, GET login redirects to dashboard
        res = self.client.get(reverse('accounts:login'))
        self.assertEqual(res.status_code, 302)

        # Logout
        res = self.client.get(reverse('accounts:logout'))
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('accounts:login'))

    def test_change_password(self):
        self.client.force_login(self.admin)
        res = self.client.get(reverse('accounts:change_password'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('accounts:change_password'), {
            'old_password': 'pass123',
            'new_password': 'NewPassword456!',
            'confirm_password': 'NewPassword456!',
        })
        self.assertEqual(res.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.check_password('NewPassword456!'))

    def test_user_crud_views(self):
        self.client.force_login(self.admin)

        # User list & filters
        res = self.client.get(reverse('accounts:user_list'), {'q': 'acc_accountant', 'role': 'Accountant'})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'acc_accountant')

        # User create
        res = self.client.get(reverse('accounts:user_create'))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('accounts:user_create'), {
            'username': 'newuser1',
            'password': 'InitPass123!',
            'confirm_password': 'InitPass123!',
            'role': 'Driver',
            'phone': '03001112233',
            'is_active': True,
        })
        self.assertEqual(res.status_code, 302)
        new_u = User.objects.get(username='newuser1')
        self.assertEqual(new_u.role, 'Driver')

        # User edit
        res = self.client.get(reverse('accounts:user_edit', args=[new_u.id]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('accounts:user_edit', args=[new_u.id]), {
            'username': new_u.username,
            'role': 'Accountant',
            'phone': '03009998877',
            'is_active': True,
        })
        self.assertEqual(res.status_code, 302)
        new_u.refresh_from_db()
        self.assertEqual(new_u.role, 'Accountant')

        # Admin reset password
        res = self.client.get(reverse('accounts:reset_password', args=[new_u.id]))
        self.assertEqual(res.status_code, 200)

        res = self.client.post(reverse('accounts:reset_password', args=[new_u.id]), {
            'new_password': 'ResetPass789!',
            'confirm_password': 'ResetPass789!',
        })
        self.assertEqual(res.status_code, 302)
        new_u.refresh_from_db()
        self.assertTrue(new_u.check_password('ResetPass789!'))

        # Self-delete prevention
        res = self.client.post(reverse('accounts:user_delete', args=[self.admin.id]))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())

        # Delete other user
        res = self.client.get(reverse('accounts:user_delete', args=[new_u.id]))
        self.assertEqual(res.status_code, 200)
        res = self.client.post(reverse('accounts:user_delete', args=[new_u.id]))
        self.assertEqual(res.status_code, 302)
        self.assertFalse(User.objects.filter(id=new_u.id).exists())

    def test_dashboards_all_roles(self):
        # Admin dashboard
        self.client.force_login(self.admin)
        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Admin Dashboard')

        # Accountant dashboard
        self.client.force_login(self.accountant)
        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Fee Collection')

        # Driver dashboard
        self.client.force_login(self.driver)
        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)

        # Student dashboard with linked student
        self.client.force_login(self.student_user)
        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Test Accounts Stu')

        # Student dashboard without linked student
        unlinked_student = User.objects.create_user('unlinked_stu', 'unl@t.com', 'pass123', role='Student')
        self.client.force_login(unlinked_student)
        res = self.client.get(reverse('dashboard:home'))
        self.assertEqual(res.status_code, 200)
