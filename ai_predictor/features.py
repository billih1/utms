import re
from finance.models import FeePayment


def extract_semester_number(semester_str: str) -> int:
    """Helper to convert e.g. '5th', 'Semester 3' into integer 5 or 3."""
    if not semester_str:
        return 1
    nums = re.findall(r'\d+', semester_str)
    return int(nums[0]) if nums else 1


def extract_student_features(student) -> dict:
    """
    GAP 4 RESOLUTION: Feature extraction for AI Defaulter Prediction.
    Features:
    - total_months: Total historical fee entries
    - paid_months: Total months marked Paid
    - unpaid_months: Total months marked Unpaid
    - payment_ratio: paid / total (1.0 if clean)
    - consecutive_defaults: current streak of unpaid fees
    - route_rent: nominal monthly rent amount
    - semester_num: numeric semester
    """
    payments = FeePayment.objects.filter(student=student).order_by('created_at')

    total = payments.count()
    paid = payments.filter(status='Paid').count()
    unpaid = payments.filter(status='Unpaid').count()

    # Consecutive streak of unpaid months ending at latest
    consecutive = 0
    for p in payments.order_by('-created_at'):
        if p.status == 'Unpaid':
            consecutive += 1
        else:
            break

    ratio = (paid / total) if total > 0 else 1.0
    rent = float(student.route.rent) if (student.route and student.route.rent) else 5000.0
    sem = extract_semester_number(student.semester)

    return {
        'total_months': total,
        'paid_months': paid,
        'unpaid_months': unpaid,
        'payment_ratio': round(ratio, 2),
        'consecutive_defaults': consecutive,
        'route_rent': rent,
        'semester_num': sem,
    }
