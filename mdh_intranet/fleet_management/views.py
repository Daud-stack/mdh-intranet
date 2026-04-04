from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Vehicle, TripLog, FuelLog
from .forms import TripLogForm, EndTripForm, FuelLogForm

@login_required
def dashboard(request):
    """Fleet Management Home"""
    active_trips = TripLog.objects.filter(end_time__isnull=True).select_related('vehicle', 'driver')
    available_vehicles = Vehicle.objects.filter(status='AVAILABLE').count()
    maintenance_vehicles = Vehicle.objects.filter(status='MAINTENANCE').count()
    
    # Simple alert logic - vehicles close to expiry
    thirty_days = timezone.now().date() + timezone.timedelta(days=30)
    renewals = Vehicle.objects.filter(next_service_date__lte=thirty_days)

    context = {
        'active_trips': active_trips,
        'available_count': available_vehicles,
        'maintenance_count': maintenance_vehicles,
        'renewals': renewals,
    }
    return render(request, 'fleet_management/dashboard.html', context)

@login_required
def start_trip(request):
    """Log the beginning of a dispatch/trip"""
    if request.method == 'POST':
        form = TripLogForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.driver = request.user
            
            # Update Vehicle Status
            vehicle = trip.vehicle
            vehicle.status = 'IN_TRANSIT'
            vehicle.save()
            
            trip.save()
            messages.success(request, f"Trip started in {vehicle.license_plate}. Drive safely.")
            return redirect('fleet_management:dashboard')
    else:
        # Pre-fill with the first available vehicle
        first_avail = Vehicle.objects.filter(status='AVAILABLE').first()
        initial = {}
        if first_avail:
            initial['vehicle'] = first_avail
            initial['start_mileage'] = first_avail.current_mileage
        form = TripLogForm(initial=initial)

    return render(request, 'fleet_management/start_trip.html', {'form': form})

@login_required
def end_trip(request, pk):
    """Complete an active trip"""
    trip = get_object_or_404(TripLog, pk=pk, driver=request.user, end_time__isnull=True)
    if request.method == 'POST':
        form = EndTripForm(request.POST, instance=trip)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.end_time = timezone.now()
            
            # Update Vehicle Status and Mileage
            vehicle = trip.vehicle
            vehicle.status = 'AVAILABLE'
            if trip.end_mileage:
                vehicle.current_mileage = trip.end_mileage
            vehicle.save()
            
            trip.save()
            messages.success(request, "Trip completed successfully.")
            return redirect('fleet_management:dashboard')
    else:
        form = EndTripForm(instance=trip)
        
    return render(request, 'fleet_management/end_trip.html', {'form': form, 'trip': trip})

@login_required
def vehicle_list(request):
    """Complete directory of all vehicles"""
    vehicles = Vehicle.objects.all().order_by('-status', 'vehicle_type')
    return render(request, 'fleet_management/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_detail(request, pk):
    """Detailed view for a specific vehicle, showing history"""
    vehicle = get_object_or_404(Vehicle, pk=pk)
    trips = vehicle.trips.all().order_by('-start_time')[:10]
    fuel_logs = vehicle.fuel_logs.all().order_by('-date')[:5]
    return render(request, 'fleet_management/vehicle_detail.html', {
        'vehicle': vehicle,
        'trips': trips,
        'fuel_logs': fuel_logs
    })

@login_required
def log_fuel(request):
    """Log a refueling event"""
    if request.method == 'POST':
        form = FuelLogForm(request.POST, request.FILES)
        if form.is_valid():
            fuel = form.save(commit=False)
            fuel.logged_by = request.user
            fuel.save()
            messages.success(request, f"Logged {fuel.liters}L for {fuel.vehicle.license_plate}.")
            return redirect('fleet_management:vehicle_detail', pk=fuel.vehicle.pk)
    else:
        form = FuelLogForm()
    return render(request, 'fleet_management/log_fuel.html', {'form': form})
