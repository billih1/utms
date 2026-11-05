from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from accounts.decorators import driver_required, admin_required
from transport.models import Van
from .models import VehicleLog
from .forms import DriverLogForm


@driver_required
def driver_panel(request):
    """
    UC-18: Driver panel to record trip departure, arrival, and operational status.
    """
    if request.method == 'POST':
        form = DriverLogForm(request.POST)
        if form.is_valid():
            log = form.save(commit=False)
            log.driver = request.user
            log.save()
            messages.success(request, f"Status updated for Van '{log.van.van_number}'. Entry saved to vehicle log.")
            return redirect('operations:driver_panel')
    else:
        form = DriverLogForm()

    today_logs = VehicleLog.objects.filter(driver=request.user).select_related('van', 'route')[:10]
    return render(request, 'operations/driver_panel.html', {
        'form': form,
        'today_logs': today_logs,
    })


@admin_required
def vehicle_log_list(request):
    """
    UC-17: Admin view to inspect full vehicle movement logs.
    """
    date = request.GET.get('date', '').strip()
    van_id = request.GET.get('van', '').strip()

    logs = VehicleLog.objects.select_related('van', 'route', 'driver').all()
    if date:
        logs = logs.filter(date=date)
    if van_id:
        logs = logs.filter(van_id=van_id)

    vans = Van.objects.filter(is_active=True)

    return render(request, 'operations/vehicle_log_list.html', {
        'logs': logs,
        'vans': vans,
        'selected_date': date,
        'selected_van': van_id,
    })
