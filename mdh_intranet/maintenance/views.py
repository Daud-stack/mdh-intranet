from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum
from .models import Asset, WorkOrder, AssetReading, MaintenanceTask
from .forms import WorkOrderForm, AssetReadingForm, AssetForm
from django.utils import timezone
from datetime import timedelta

@login_required
def dashboard(request):
    """Overview of maintenance activities"""
    open_orders = WorkOrder.objects.exclude(status='COMPLETED').order_by('-priority', 'created_at')
    recent_readings = AssetReading.objects.all().select_related('asset')[:10]
    critical_assets = Asset.objects.filter(status='DOWN')
    
    # Simple predictive logic: assets with temperature readings > 70 in last 24h
    yesterday = timezone.now() - timedelta(days=1)
    predictive_alerts = AssetReading.objects.filter(
        reading_type__icontains='temp', 
        value__gt=70, 
        timestamp__gt=yesterday
    ).select_related('asset')
    
    context = {
        'open_orders': open_orders,
        'recent_readings': recent_readings,
        'critical_assets': critical_assets,
        'predictive_alerts': predictive_alerts,
        'stats': {
            'total_assets': Asset.objects.count(),
            'pending_ppm': Asset.objects.filter(next_ppm_date__lte=timezone.now().date()).count(),
            'open_wo': WorkOrder.objects.filter(status__in=['OPEN', 'ASSIGNED', 'IN_PROGRESS']).count(),
        }
    }
    return render(request, 'maintenance/dashboard.html', context)

@login_required
def asset_list(request):
    """List of all hospital assets"""
    assets = Asset.objects.all().order_by('category', 'name')
    return render(request, 'maintenance/asset_list.html', {'assets': assets})

@login_required
def asset_detail(request, pk):
    """Deep dive into one asset's history and health"""
    asset = get_object_or_404(Asset, pk=pk)
    work_orders = asset.work_orders.all().order_by('-created_at')
    readings = asset.readings.all().order_by('-timestamp')[:20]
    
    if request.method == 'POST' and 'reading' in request.POST:
        r_form = AssetReadingForm(request.POST)
        if r_form.is_valid():
            reading = r_form.save(commit=False)
            reading.asset = asset
            reading.save()
            messages.success(request, f"Stored {reading.reading_type} reading for predictive analysis.")
            return redirect('maintenance:asset_detail', pk=asset.pk)
    else:
        r_form = AssetReadingForm()
        
    return render(request, 'maintenance/asset_detail.html', {
        'asset': asset,
        'work_orders': work_orders,
        'readings': readings,
        'r_form': r_form
    })

@login_required
def work_order_create(request, asset_id=None):
    """Create a new work order"""
    asset = get_object_or_404(Asset, pk=asset_id) if asset_id else None
    if request.method == 'POST':
        form = WorkOrderForm(request.POST)
        if form.is_valid():
            wo = form.save(commit=False)
            wo.reported_by = request.user
            wo.save()
            messages.success(request, f"Work Order #{wo.id} created successfully.")
            return redirect('maintenance:dashboard')
    else:
        initial = {}
        if asset:
            initial['asset'] = asset
        form = WorkOrderForm(initial=initial)
        
    return render(request, 'maintenance/work_order_form.html', {'form': form, 'asset': asset})

@login_required
def work_order_detail(request, pk):
    """View and update a specific work order"""
    wo = get_object_or_404(WorkOrder, pk=pk)
    if request.method == 'POST' and 'status' in request.POST:
        new_status = request.POST.get('status')
        wo.status = new_status
        if new_status == 'COMPLETED':
            wo.completed_at = timezone.now()
            wo.asset.last_maintenance = timezone.now()
            wo.asset.save()
        wo.save()
        messages.success(request, f"Work Order updated to {new_status}.")
        return redirect('maintenance:work_order_detail', pk=wo.pk)
        
    return render(request, 'maintenance/work_order_detail.html', {'wo': wo})

@login_required
def asset_create(request):
    """Add a new hospital asset"""
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save()
            messages.success(request, f"Asset {asset.name} added successfully.")
            return redirect('maintenance:asset_list')
    else:
        form = AssetForm()
        
    return render(request, 'maintenance/asset_form.html', {'form': form})

@login_required
def asset_update(request, pk):
    """Update an existing hospital asset"""
    asset = get_object_or_404(Asset, pk=pk)
    if request.method == 'POST':
        form = AssetForm(request.POST, instance=asset)
        if form.is_valid():
            form.save()
            messages.success(request, f"Asset {asset.name} updated successfully.")
            return redirect('maintenance:asset_detail', pk=asset.pk)
    else:
        form = AssetForm(instance=asset)
        
    return render(request, 'maintenance/asset_form.html', {'form': form, 'is_update': True, 'asset': asset})
