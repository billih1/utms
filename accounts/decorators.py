from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages


def role_required(*allowed_roles):
    """
    Decorator for views that checks if the logged in user has one of the allowed roles.
    Admins/superusers always pass.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_superuser or request.user.role == 'Admin':
                return view_func(request, *args, **kwargs)
            if request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, f"Access denied. Required role: {', '.join(allowed_roles)}")
            raise PermissionDenied("You do not have permission to access this page.")
        return _wrapped_view
    return decorator


def admin_required(view_func):
    return role_required('Admin')(view_func)


def accountant_required(view_func):
    return role_required('Admin', 'Accountant')(view_func)


def driver_required(view_func):
    return role_required('Admin', 'Driver')(view_func)


def student_required(view_func):
    return role_required('Admin', 'Student')(view_func)
