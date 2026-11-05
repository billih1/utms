from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime

from .models import User
from .forms import LoginForm, UserCreateForm, UserUpdateForm, ChangePasswordForm, AdminResetPasswordForm
from .decorators import admin_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('dashboard:home')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.user, request.POST)
        if form.is_valid():
            request.user.set_password(form.cleaned_data['new_password'])
            request.user.save()
            messages.success(request, "Password updated successfully. Please log in again.")
            return redirect('accounts:login')
    else:
        form = ChangePasswordForm(request.user)

    return render(request, 'accounts/change_password.html', {'form': form})


@admin_required
def user_list_view(request):
    query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()

    users = User.objects.all()
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'accounts/user_list.html', {
        'users': users,
        'query': query,
        'role_filter': role_filter,
        'roles': User.Role.choices,
    })


@admin_required
def user_create_view(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"User '{user.username}' created successfully.")
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create New User'})


@admin_required
def user_edit_view(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user_obj)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{user_obj.username}' updated.")
            return redirect('accounts:user_list')
    else:
        form = UserUpdateForm(instance=user_obj)

    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit User: {user_obj.username}'})


@admin_required
def user_delete_view(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if user_obj == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('accounts:user_list')

    if request.method == 'POST':
        username = user_obj.username
        user_obj.delete()
        messages.success(request, f"User '{username}' was deleted.")
        return redirect('accounts:user_list')

    return render(request, 'accounts/user_confirm_delete.html', {'user_obj': user_obj})


@admin_required
def reset_password_view(request, pk):
    user_obj = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = AdminResetPasswordForm(request.POST)
        if form.is_valid():
            user_obj.set_password(form.cleaned_data['new_password'])
            user_obj.save()
            messages.success(request, f"Password reset for {user_obj.username}.")
            return redirect('accounts:user_list')
    else:
        form = AdminResetPasswordForm()

    return render(request, 'accounts/reset_password.html', {'form': form, 'target_user': user_obj})


@login_required
def dashboard_view(request):
    role = getattr(request.user, 'role', 'Student')

    # Lazy imports to avoid circular dependency
    from students.models import Student
    from transport.models import Route, Van
    from finance.models import FeePayment
    from operations.models import VehicleLog

    current_month_str = timezone.now().strftime("%b %Y")

    if role == 'Admin' or request.user.is_superuser:
        total_students = Student.objects.filter(is_active=True).count()
        total_vans = Van.objects.filter(is_active=True).count()
        total_routes = Route.objects.filter(is_active=True).count()

        current_month_payments = FeePayment.objects.filter(month=current_month_str)
        collected = current_month_payments.filter(status='Paid').aggregate(s=Sum('amount_paid'))['s'] or 0
        due = current_month_payments.filter(status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0

        recent_payments = FeePayment.objects.filter(status='Paid').select_related('student', 'student__route').order_by('-paid_at')[:5]
        defaulters = current_month_payments.filter(status='Unpaid').select_related('student', 'student__route')[:5]

        context = {
            'role': 'Admin',
            'current_month': current_month_str,
            'total_students': total_students,
            'total_vans': total_vans,
            'total_routes': total_routes,
            'collected_amount': collected,
            'due_amount': due,
            'recent_payments': recent_payments,
            'defaulters': defaulters,
        }
        return render(request, 'dashboard/admin.html', context)

    elif role == 'Accountant':
        current_month_payments = FeePayment.objects.filter(month=current_month_str)
        collected = current_month_payments.filter(status='Paid').aggregate(s=Sum('amount_paid'))['s'] or 0
        due = current_month_payments.filter(status='Unpaid').aggregate(s=Sum('amount'))['s'] or 0
        unpaid_count = current_month_payments.filter(status='Unpaid').count()
        paid_count = current_month_payments.filter(status='Paid').count()

        recent_payments = FeePayment.objects.filter(status='Paid').select_related('student').order_by('-paid_at')[:8]
        context = {
            'role': 'Accountant',
            'current_month': current_month_str,
            'collected_amount': collected,
            'due_amount': due,
            'unpaid_count': unpaid_count,
            'paid_count': paid_count,
            'recent_payments': recent_payments,
        }
        return render(request, 'dashboard/accountant.html', context)

    elif role == 'Driver':
        # Find driver's assigned van or logs
        logs = VehicleLog.objects.filter(driver=request.user).select_related('van', 'route').order_by('-created_at')[:10]
        context = {
            'role': 'Driver',
            'recent_logs': logs,
        }
        return render(request, 'dashboard/driver.html', context)

    else:  # Student
        student_obj = None
        fee_records = []
        if request.user.linked_student_id:
            try:
                student_obj = Student.objects.select_related('route', 'van').get(pk=request.user.linked_student_id)
                fee_records = student_obj.fee_payments.all().order_by('-created_at')
            except Student.DoesNotExist:
                pass
        context = {
            'role': 'Student',
            'student': student_obj,
            'fee_records': fee_records,
        }
        return render(request, 'dashboard/student.html', context)
