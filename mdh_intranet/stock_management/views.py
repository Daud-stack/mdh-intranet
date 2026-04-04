from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import models as django_models
from .models import StockCategory, StockItem, Requisition, RequisitionItem, StockOrder


@login_required
def index(request):
    """Stock management dashboard"""
    low_stock_items = StockItem.objects.filter(current_quantity__lte=django_models.F('min_threshold'))
    pending_requisitions = Requisition.objects.filter(status='pending')
    recent_orders = StockOrder.objects.all()[:5]
    
    # Count user's requisitions
    user_requisitions_count = Requisition.objects.filter(requested_by=request.user).count()
    
    context = {
        'total_items': StockItem.objects.count(),
        'low_stock_count': low_stock_items.count(),
        'pending_count': pending_requisitions.count(),
        'low_stock_items': low_stock_items[:10],
        'pending_requisitions': pending_requisitions[:5],
        'recent_orders': recent_orders,
        'user_requisitions_count': user_requisitions_count,
    }
    return render(request, 'stock_management/index.html', context)


@login_required
def stock_list(request):
    """Browse all stock items"""
    category_filter = request.GET.get('category')
    search = request.GET.get('search')
    
    items = StockItem.objects.select_related('category').all()
    
    if category_filter:
        items = items.filter(category_id=category_filter)
    
    if search:
        items = items.filter(name__icontains=search)
    
    categories = StockCategory.objects.all()
    
    context = {
        'items': items,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search,
    }
    return render(request, 'stock_management/stock_list.html', context)


@login_required
def create_requisition(request):
    """Create a new internal requisition"""
    if request.method == 'POST':
        department = request.POST.get('department')
        justification = request.POST.get('justification')
        
        # Create requisition
        requisition = Requisition.objects.create(
            requested_by=request.user,
            department=department,
            justification=justification,
        )
        
        # Add items
        item_ids = request.POST.getlist('item_id[]')
        quantities = request.POST.getlist('quantity[]')
        notes_list = request.POST.getlist('notes[]')
        
        for item_id, quantity, item_notes in zip(item_ids, quantities, notes_list):
            if item_id and quantity:
                RequisitionItem.objects.create(
                    requisition=requisition,
                    stock_item_id=item_id,
                    quantity_requested=int(quantity),
                    notes=item_notes or '',
                )
        
        from mdh_intranet.core.services import notify_admins
        notify_admins(
            title="New Stock Requisition",
            notification_type="approval",
            message=f"{request.user.username} requested new stock items for {requisition.department}.",
            link=f"/stock/requisition/{requisition.pk}/",
            priority="normal"
        )
        
        messages.success(request, f'Requisition {requisition.requisition_number} created successfully!')
        return redirect('stock_management:requisition_detail', pk=requisition.pk)
    
    stock_items = StockItem.objects.select_related('category').all()
    context = {
        'stock_items': stock_items,
        'departments': Requisition.DEPARTMENT_CHOICES,
    }
    return render(request, 'stock_management/create_requisition.html', context)


@login_required
def my_requisitions(request):
    """View user's requisition history"""
    requisitions = Requisition.objects.filter(requested_by=request.user).prefetch_related('items')
    
    context = {
        'requisitions': requisitions,
    }
    return render(request, 'stock_management/my_requisitions.html', context)


@login_required
def requisition_detail(request, pk):
    """View requisition details"""
    requisition = get_object_or_404(
        Requisition.objects.prefetch_related('items__stock_item'),
        pk=pk
    )
    
    context = {
        'requisition': requisition,
        'can_approve': request.user.is_staff and requisition.can_approve,
    }
    return render(request, 'stock_management/requisition_detail.html', context)


@login_required
def approve_requisition(request, pk):
    """Approve a requisition (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to approve requisitions.')
        return redirect('stock_management:requisition_detail', pk=pk)
    
    requisition = get_object_or_404(Requisition, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            requisition.status = 'approved'
            requisition.approved_by = request.user
            requisition.approved_at = timezone.now()
            requisition.save()
            
            from mdh_intranet.core.services import notify
            notify(
                recipient=requisition.requested_by,
                title=f"Requisition Approved",
                notification_type="approved",
                message=f"Your stock requisition {requisition.requisition_number} has been approved by {request.user.username}.",
                link=f"/stock/requisition/{requisition.pk}/",
                priority="normal"
            )
            
            messages.success(request, f'Requisition {requisition.requisition_number} approved!')
        
        elif action == 'reject':
            requisition.status = 'rejected'
            requisition.rejection_reason = request.POST.get('rejection_reason', '')
            requisition.approved_by = request.user
            requisition.approved_at = timezone.now()
            requisition.save()
            
            from mdh_intranet.core.services import notify
            notify(
                recipient=requisition.requested_by,
                title=f"Requisition Rejected",
                notification_type="rejected",
                message=f"Your stock requisition {requisition.requisition_number} was rejected by {request.user.username}.",
                link=f"/stock/requisition/{requisition.pk}/",
                priority="high"
            )
            
            messages.warning(request, f'Requisition {requisition.requisition_number} rejected.')
        
        return redirect('stock_management:requisition_detail', pk=pk)
    
    return redirect('stock_management:requisition_detail', pk=pk)


@login_required
def pending_approvals(request):
    """View all pending requisitions (staff only)"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('stock_management:index')
    
    pending = Requisition.objects.filter(status='pending').prefetch_related('items')
    
    context = {
        'requisitions': pending,
    }
    return render(request, 'stock_management/pending_approvals.html', context)
