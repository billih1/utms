from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import admin_required
from .models import Route, Van
from .forms import RouteForm, VanForm


@admin_required
def route_list(request):
    routes = Route.objects.prefetch_related('vans', 'students').all()
    return render(request, 'transport/route_list.html', {'routes': routes})


@admin_required
def route_create(request):
    if request.method == 'POST':
        form = RouteForm(request.POST)
        if form.is_valid():
            route = form.save()
            messages.success(request, f"Route '{route.route_name}' created successfully.")
            return redirect('transport:route_list')
    else:
        form = RouteForm()
    return render(request, 'transport/route_form.html', {'form': form, 'title': 'Add New Route'})


@admin_required
def route_edit(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if request.method == 'POST':
        form = RouteForm(request.POST, instance=route)
        if form.is_valid():
            form.save()
            messages.success(request, f"Route '{route.route_name}' updated.")
            return redirect('transport:route_list')
    else:
        form = RouteForm(instance=route)
    return render(request, 'transport/route_form.html', {'form': form, 'title': f'Edit Route: {route.route_name}'})


@admin_required
def route_delete(request, pk):
    route = get_object_or_404(Route, pk=pk)
    if route.students.filter(is_active=True).exists():
        messages.error(request, f"Cannot delete route '{route.route_name}' because students are currently assigned to it.")
        return redirect('transport:route_list')

    if request.method == 'POST':
        name = route.route_name
        route.delete()
        messages.success(request, f"Route '{name}' deleted.")
        return redirect('transport:route_list')
    return render(request, 'transport/route_confirm_delete.html', {'route': route})


@admin_required
def van_list(request):
    vans = Van.objects.select_related('route').prefetch_related('students').all()
    return render(request, 'transport/van_list.html', {'vans': vans})


@admin_required
def van_create(request):
    if request.method == 'POST':
        form = VanForm(request.POST)
        if form.is_valid():
            van = form.save()
            messages.success(request, f"Van '{van.van_number}' added successfully.")
            return redirect('transport:van_list')
    else:
        form = VanForm()
    return render(request, 'transport/van_form.html', {'form': form, 'title': 'Add New Van / Spare Vehicle'})


@admin_required
def van_edit(request, pk):
    van = get_object_or_404(Van, pk=pk)
    if request.method == 'POST':
        form = VanForm(request.POST, instance=van)
        if form.is_valid():
            form.save()
            messages.success(request, f"Van '{van.van_number}' updated.")
            return redirect('transport:van_list')
    else:
        form = VanForm(instance=van)
    return render(request, 'transport/van_form.html', {'form': form, 'title': f'Edit Van: {van.van_number}'})


@admin_required
def van_delete(request, pk):
    van = get_object_or_404(Van, pk=pk)
    if van.students.filter(is_active=True).exists():
        messages.error(request, f"Cannot delete van '{van.van_number}' because students are currently assigned to it.")
        return redirect('transport:van_list')

    if request.method == 'POST':
        vnum = van.van_number
        van.delete()
        messages.success(request, f"Van '{vnum}' deleted.")
        return redirect('transport:van_list')
    return render(request, 'transport/van_confirm_delete.html', {'van': van})
