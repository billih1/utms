import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from django.shortcuts import render
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from accounts.decorators import accountant_required
from finance.models import FeePayment
from transport.models import Route
from students.models import Student


@accountant_required
def monthly_collection(request):
    """
    FR-16 / UC-14: Monthly collection aggregated per route.
    """
    month = request.GET.get('month', '').strip()
    if not month:
        month = timezone.now().strftime("%b %Y")

    routes = Route.objects.filter(is_active=True)
    report_rows = []
    total_collected = 0
    total_remaining = 0
    total_students_enrolled = 0

    for r in routes:
        payments = FeePayment.objects.filter(student__route=r, month__iexact=month)
        collected = payments.filter(status='Paid').aggregate(s=Sum('amount_paid'))['s'] or 0
        remaining = payments.filter(status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0
        student_count = payments.count()

        total_collected += collected
        total_remaining += remaining
        total_students_enrolled += student_count

        report_rows.append({
            'route': r,
            'student_count': student_count,
            'collected': collected,
            'remaining': remaining,
        })

    all_months = FeePayment.objects.values_list('month', flat=True).distinct()

    return render(request, 'reports/monthly_collection.html', {
        'selected_month': month,
        'report_rows': report_rows,
        'total_collected': total_collected,
        'total_remaining': total_remaining,
        'total_students': total_students_enrolled,
        'all_months': all_months,
    })


@accountant_required
def due_remaining(request):
    """
    FR-17 / UC-15: Outstanding dues list per student and route.
    """
    month = request.GET.get('month', '').strip()
    if not month:
        month = timezone.now().strftime("%b %Y")

    dues = FeePayment.objects.filter(month__iexact=month, status='Unpaid').select_related(
        'student', 'student__route', 'student__van'
    )
    total_due = dues.aggregate(s=Sum('amount'))['s'] or 0
    all_months = FeePayment.objects.values_list('month', flat=True).distinct()

    return render(request, 'reports/due_remaining.html', {
        'selected_month': month,
        'dues': dues,
        'total_due': total_due,
        'all_months': all_months,
    })


@accountant_required
def defaulter_report(request):
    """
    FR-18 / UC-16: Monthly defaulter report with months count and total amount owed.
    """
    month = request.GET.get('month', '').strip()
    if not month:
        month = timezone.now().strftime("%b %Y")

    # Fetch unpaid fee payments for the chosen month
    current_month_unpaid = FeePayment.objects.filter(month__iexact=month, status='Unpaid').select_related(
        'student', 'student__route', 'student__van'
    )

    defaulters_data = []
    total_defaulter_due = 0

    for fee in current_month_unpaid:
        student = fee.student
        # Calculate total unpaid months historically for this student
        total_unpaid_months = FeePayment.objects.filter(student=student, status='Unpaid').count()
        total_owed = FeePayment.objects.filter(student=student, status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0

        total_defaulter_due += total_owed
        defaulters_data.append({
            'student': student,
            'current_month_fee': fee,
            'unpaid_months_count': total_unpaid_months,
            'total_due': total_owed,
        })

    all_months = FeePayment.objects.values_list('month', flat=True).distinct()

    return render(request, 'reports/defaulter_report.html', {
        'selected_month': month,
        'defaulters': defaulters_data,
        'total_defaulter_due': total_defaulter_due,
        'total_count': len(defaulters_data),
        'all_months': all_months,
    })


@accountant_required
def export_excel(request):
    """
    FR-25: Export Defaulter / Collection Report as an Excel (.xlsx) file.
    """
    report_type = request.GET.get('type', 'defaulters')
    month = request.GET.get('month', timezone.now().strftime("%b %Y"))

    wb = openpyxl.Workbook()
    ws = wb.active

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")

    if report_type == 'defaulters':
        ws.title = f"Defaulters_{month}"
        headers = ["Adm No", "Student Name", "Program", "Semester", "Route", "Van", "Unpaid Months", "Total Due (PKR)"]
        ws.append(headers)

        unpaid = FeePayment.objects.filter(month__iexact=month, status='Unpaid').select_related(
            'student', 'student__route', 'student__van'
        )
        for fee in unpaid:
            st = fee.student
            unpaid_count = FeePayment.objects.filter(student=st, status='Unpaid').count()
            total_owed = FeePayment.objects.filter(student=st, status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0
            ws.append([
                st.admission_number,
                st.name,
                st.program,
                st.semester,
                st.route.route_name if st.route else 'N/A',
                st.van.van_number if st.van else 'N/A',
                unpaid_count,
                float(total_owed)
            ])
    else:
        ws.title = f"Collection_{month}"
        headers = ["Route Name", "Rent (PKR)", "Enrolled Students", "Collected (PKR)", "Remaining (PKR)"]
        ws.append(headers)

        routes = Route.objects.filter(is_active=True)
        for r in routes:
            payments = FeePayment.objects.filter(student__route=r, month__iexact=month)
            collected = payments.filter(status='Paid').aggregate(s=Sum('amount_paid'))['s'] or 0
            remaining = payments.filter(status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0
            ws.append([
                r.route_name,
                float(r.rent),
                payments.count(),
                float(collected),
                float(remaining)
            ])

    # Format header row
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    filename = f"TMS_{report_type}_{month.replace(' ', '_')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    return response
