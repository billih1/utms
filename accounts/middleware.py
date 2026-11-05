import time
from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect


class SessionTimeoutMiddleware:
    """
    NFR-S3: Session timeout middleware after inactivity (default 30 mins).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            current_time = time.time()
            last_activity = request.session.get('last_activity')

            timeout = getattr(settings, 'SESSION_COOKIE_AGE', 1800)  # 30 mins
            if last_activity and (current_time - last_activity > timeout):
                logout(request)
                messages.warning(request, "Your session has expired due to inactivity. Please log in again.")
                return redirect('accounts:login')

            request.session['last_activity'] = current_time

        response = self.get_response(request)
        return response


class RoleMiddleware:
    """
    Attaches convenient role flags to request.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.user_role = getattr(request.user, 'role', 'Student')
        else:
            request.user_role = None

        return self.get_response(request)
