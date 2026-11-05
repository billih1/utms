import os
import django
from decimal import Decimal
from datetime import datetime, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tms.settings')
django.setup()

from django.utils import timezone
from accounts.models import User
from transport.models import Route, Van
from students.models import Student
from finance.models import FeePayment
from finance.services import get_or_create_voucher, get_or_create_challan, record_payment
from operations.models import VehicleLog
from ai_predictor.model import train_defaulter_model, run_prediction_for_month


def seed():
    print("--> Seeding Demo Data for UTMS (aligned with SRS)...")

    # 1. Routes
    r1, _ = Route.objects.get_or_create(route_name="Daska - GCUF", defaults={'rent': Decimal('5000.00'), 'description': 'Main terminal to Allama Iqbal Campus'})
    r2, _ = Route.objects.get_or_create(route_name="Sialkot - GCUF", defaults={'rent': Decimal('7000.00'), 'description': 'Cantt to Main Campus'})
    r3, _ = Route.objects.get_or_create(route_name="Gujranwala - GCUF", defaults={'rent': Decimal('6500.00'), 'description': 'Bypass to GCUF New Campus'})

    # 2. Vans
    v1, _ = Van.objects.get_or_create(van_number="LEA-101", defaults={'capacity': 22, 'route': r1})
    v2, _ = Van.objects.get_or_create(van_number="LEB-202", defaults={'capacity': 20, 'route': r2})
    v3, _ = Van.objects.get_or_create(van_number="LEC-303", defaults={'capacity': 22, 'route': None}) # Spare vehicle

    # 3. Students
    s1, _ = Student.objects.get_or_create(admission_number="2022-101", defaults={'name': "Ali Khan", 'program': "BSIT", 'semester': "5th", 'phone': "0300-1112233", 'route': r1, 'van': v1})
    s2, _ = Student.objects.get_or_create(admission_number="2022-245", defaults={'name': "Sara", 'program': "BSCS", 'semester': "3rd", 'phone': "0301-2223344", 'route': r2, 'van': v2})
    s3, _ = Student.objects.get_or_create(admission_number="2023-017", defaults={'name': "Ahmed", 'program': "BSIT", 'semester': "3rd", 'phone': "0302-3334455", 'route': r1, 'van': v1})
    s4, _ = Student.objects.get_or_create(admission_number="2023-052", defaults={'name': "Hina", 'program': "BSIT", 'semester': "1st", 'phone': "0303-4445566", 'route': r3, 'van': v3})

    # 4. Users (Role Based Access Control)
    # Admin
    if not User.objects.filter(username="admin").exists():
        admin_u = User.objects.create_superuser("admin", "admin@gcuf.edu.pk", "admin123")
        admin_u.role = User.Role.ADMIN
        admin_u.phone = "0300-0000001"
        admin_u.save()

    # Accountant
    if not User.objects.filter(username="accountant").exists():
        acc_u = User.objects.create_user("accountant", "accountant@gcuf.edu.pk", "accountant123")
        acc_u.role = User.Role.ACCOUNTANT
        acc_u.phone = "0300-0000002"
        acc_u.save()

    # Driver
    if not User.objects.filter(username="driver").exists():
        drv_u = User.objects.create_user("driver", "driver@gcuf.edu.pk", "driver123")
        drv_u.role = User.Role.DRIVER
        drv_u.phone = "0300-0000003"
        drv_u.linked_driver_info = "Driver A (LEA-101)"
        drv_u.save()
    else:
        drv_u = User.objects.get(username="driver")

    # Student User
    if not User.objects.filter(username="student").exists():
        stu_u = User.objects.create_user("student", "student@gcuf.edu.pk", "student123")
        stu_u.role = User.Role.STUDENT
        stu_u.phone = "0300-1112233"
        stu_u.linked_student_id = s1.id
        stu_u.save()

    # 5. Fee Payments History (for ML Defaulter model & Reports)
    # Ali Khan: Aug (Paid), Sep (Paid), Oct (Unpaid)
    p_aug1, _ = FeePayment.objects.get_or_create(student=s1, month="August 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('5000.00'), 'status': FeePayment.Status.PAID, 'paid_at': timezone.now()})
    p_sep1, _ = FeePayment.objects.get_or_create(student=s1, month="September 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('5000.00'), 'status': FeePayment.Status.PAID, 'paid_at': timezone.now()})
    p_oct1, _ = FeePayment.objects.get_or_create(student=s1, month="October 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('0.00'), 'status': FeePayment.Status.UNPAID})

    # Sara: Aug (Paid), Sep (Paid), Oct (Unpaid)
    p_aug2, _ = FeePayment.objects.get_or_create(student=s2, month="August 2026", defaults={'amount': Decimal('7000.00'), 'amount_paid': Decimal('7000.00'), 'status': FeePayment.Status.PAID, 'paid_at': timezone.now()})
    p_sep2, _ = FeePayment.objects.get_or_create(student=s2, month="September 2026", defaults={'amount': Decimal('7000.00'), 'amount_paid': Decimal('7000.00'), 'status': FeePayment.Status.PAID, 'paid_at': timezone.now()})
    p_oct2, _ = FeePayment.objects.get_or_create(student=s2, month="October 2026", defaults={'amount': Decimal('7000.00'), 'amount_paid': Decimal('0.00'), 'status': FeePayment.Status.UNPAID})

    # Ahmed: Aug (Unpaid), Sep (Unpaid), Oct (Unpaid) -> 3 Consecutive Defaulter
    p_aug3, _ = FeePayment.objects.get_or_create(student=s3, month="August 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('0.00'), 'status': FeePayment.Status.UNPAID})
    p_sep3, _ = FeePayment.objects.get_or_create(student=s3, month="September 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('0.00'), 'status': FeePayment.Status.UNPAID})
    p_oct3, _ = FeePayment.objects.get_or_create(student=s3, month="October 2026", defaults={'amount': Decimal('5000.00'), 'amount_paid': Decimal('0.00'), 'status': FeePayment.Status.UNPAID})

    # Hina: Oct (Paid)
    p_oct4, _ = FeePayment.objects.get_or_create(student=s4, month="October 2026", defaults={'amount': Decimal('6500.00'), 'amount_paid': Decimal('6500.00'), 'status': FeePayment.Status.PAID, 'paid_at': timezone.now()})

    # 6. Generate QR Vouchers, Challans, Receipts
    get_or_create_voucher(p_oct1)
    get_or_create_challan(p_oct1)
    record_payment(p_sep1, Decimal('5000.00'))

    # 7. Vehicle Log
    VehicleLog.objects.get_or_create(
        van=v1,
        route=r1,
        driver=drv_u,
        defaults={
            'departure_time': time(7, 0),
            'arrival_time': time(7, 55),
            'status': VehicleLog.TripStatus.ARRIVED,
            'notes': 'Normal commute run, arrived on time.'
        }
    )

    # 8. Train Defaulter Model & Generate Insights
    train_defaulter_model()
    run_prediction_for_month("November 2026")

    print("[OK] Demo data seeded successfully!")
    print("   Accounts ready:")
    print("   - Admin:      admin / admin123")
    print("   - Accountant: accountant / accountant123")
    print("   - Driver:     driver / driver123")
    print("   - Student:    student / student123")


if __name__ == '__main__':
    seed()
