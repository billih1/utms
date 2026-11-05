import csv
import io
import openpyxl
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from accounts.decorators import admin_required
from transport.models import Route, Van
from .models import Student
from .forms import StudentForm, StudentAssignForm


@admin_required
def student_list(request):
    search = request.GET.get('search', '').strip()
    program = request.GET.get('program', '').strip()
    semester = request.GET.get('semester', '').strip()
    route_id = request.GET.get('route', '').strip()
    van_id = request.GET.get('van', '').strip()
    status = request.GET.get('status', '').strip()

    students = Student.objects.select_related('route', 'van').all()

    if search:
        students = students.filter(
            Q(admission_number__icontains=search) |
            Q(name__icontains=search) |
            Q(phone__icontains=search)
        )
    if program:
        students = students.filter(program__iexact=program)
    if semester:
        students = students.filter(semester__iexact=semester)
    if route_id:
        students = students.filter(route_id=route_id)
    if van_id:
        students = students.filter(van_id=van_id)
    if status == 'active':
        students = students.filter(is_active=True)
    elif status == 'inactive':
        students = students.filter(is_active=False)

    routes = Route.objects.filter(is_active=True)
    vans = Van.objects.filter(is_active=True)

    # Distinct programs and semesters for filters
    all_programs = Student.objects.values_list('program', flat=True).distinct()
    all_semesters = Student.objects.values_list('semester', flat=True).distinct()

    context = {
        'students': students,
        'search': search,
        'program': program,
        'semester': semester,
        'route_id': route_id,
        'van_id': van_id,
        'status': status,
        'routes': routes,
        'vans': vans,
        'all_programs': all_programs,
        'all_semesters': all_semesters,
    }
    return render(request, 'students/student_list.html', context)


@admin_required
def student_create(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save()
            messages.success(request, f"Student '{student.name}' ({student.admission_number}) added successfully.")
            return redirect('students:student_list')
    else:
        form = StudentForm()
    return render(request, 'students/student_form.html', {'form': form, 'title': 'Register New Student'})


@admin_required
def student_detail(request, pk):
    student = get_object_or_404(Student.objects.select_related('route', 'van'), pk=pk)
    fee_records = student.fee_payments.all().order_by('-created_at')
    return render(request, 'students/student_detail.html', {
        'student': student,
        'fee_records': fee_records,
    })


@admin_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, f"Student '{student.name}' updated.")
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentForm(instance=student)
    return render(request, 'students/student_form.html', {'form': form, 'title': f'Edit Student: {student.name}'})


@admin_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.name
        student.delete()
        messages.success(request, f"Student '{name}' was deleted.")
        return redirect('students:student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


@admin_required
def student_assign(request, pk):
    """
    UC-07: Assign student to route and van with capacity enforcement.
    """
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentAssignForm(request.POST, instance=student)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Student '{student.name}' assigned to Route '{student.route.route_name}' "
                f"and Van '{student.van.van_number}' successfully."
            )
            return redirect('students:student_detail', pk=student.pk)
    else:
        form = StudentAssignForm(instance=student)

    # Capacity info for all active vans
    vans = Van.objects.filter(is_active=True).select_related('route')

    return render(request, 'students/student_assign.html', {
        'form': form,
        'student': student,
        'vans': vans,
    })


def get_vans_for_route(request, route_id):
    """HTMX endpoint for dynamic van dropdown filtering."""
    vans = Van.objects.filter(Q(route_id=route_id) | Q(route__isnull=True), is_active=True)
    options = ['<option value="">Select a Van / Spare</option>']
    for v in vans:
        spare_badge = " [Spare]" if v.is_spare else ""
        options.append(f'<option value="{v.id}">{v.van_number}{spare_badge} ({v.filled_seats}/{v.capacity} seats)</option>')
    return HttpResponse("\n".join(options))


@admin_required
def student_import(request):
    """
    Automatic database integration tool to bulk-import students from CSV or Excel (.xlsx).
    """
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        filename = uploaded_file.name.lower()
        created_count = 0
        updated_count = 0
        error_rows = []

        try:
            rows_data = []
            if filename.endswith('.csv'):
                decoded = uploaded_file.read().decode('utf-8-sig', errors='ignore')
                reader = csv.DictReader(io.StringIO(decoded))
                for r in reader:
                    rows_data.append(r)
            elif filename.endswith(('.xlsx', '.xls')):
                wb = openpyxl.load_workbook(uploaded_file, data_only=True)
                ws = wb.active
                headers = [str(c.value).strip().lower() if c.value else '' for c in ws[1]]
                for row in ws.iter_rows(min_row=2, values_only=True):
                    if any(row):
                        row_dict = {headers[i]: (str(row[i]).strip() if row[i] is not None else '') for i in range(len(headers)) if i < len(row)}
                        rows_data.append(row_dict)
            else:
                messages.error(request, "Unsupported format. Please upload a .csv or .xlsx file.")
                return redirect('students:student_import')

            for idx, r in enumerate(rows_data, start=2):
                adm_no = (r.get('admission_number') or r.get('admission_no') or r.get('adm_no') or '').strip()
                name = (r.get('name') or r.get('student_name') or '').strip()
                program = (r.get('program') or 'BSIT').strip()
                semester = (r.get('semester') or '1st').strip()
                phone = (r.get('phone') or '').strip()
                route_name = (r.get('route') or r.get('route_name') or '').strip()
                van_num = (r.get('van') or r.get('van_number') or '').strip()

                if not adm_no or not name:
                    error_rows.append(f"Row {idx}: Missing Admission Number or Name")
                    continue

                route_obj = None
                if route_name:
                    route_obj = Route.objects.filter(route_name__icontains=route_name).first()

                van_obj = None
                if van_num:
                    van_obj = Van.objects.filter(van_number__icontains=van_num).first()

                student, created = Student.objects.update_or_create(
                    admission_number=adm_no,
                    defaults={
                        'name': name,
                        'program': program,
                        'semester': semester,
                        'phone': phone,
                        'route': route_obj,
                        'van': van_obj,
                        'is_active': True,
                    }
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1

            messages.success(
                request,
                f"Student Data Integration Complete: {created_count} registered, {updated_count} updated."
            )
            if error_rows:
                messages.warning(request, f"Warnings in {len(error_rows)} rows: {', '.join(error_rows[:3])}")

            return redirect('students:student_list')

        except Exception as e:
            messages.error(request, f"Error processing file: {str(e)}")
            return redirect('students:student_import')

    return render(request, 'students/student_import.html')
