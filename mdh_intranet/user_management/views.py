from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q


def is_superuser(user):
    """Check if user is a superuser"""
    return user.is_superuser


@login_required
@user_passes_test(is_superuser)
def index(request):
    """User management dashboard - superusers only"""
    search = request.GET.get('search', '')
    
    users = User.objects.all().order_by('-date_joined')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    context = {
        'users': users,
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'staff_users': User.objects.filter(is_staff=True).count(),
        'search_query': search,
    }
    return render(request, 'user_management/index.html', context)


@login_required
@user_passes_test(is_superuser)
def user_create(request):
    """Create a new user - superusers only"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        # Validate
        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" already exists.')
            return render(request, 'user_management/user_form.html', {'form_data': request.POST})
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_staff = is_staff
        user.is_superuser = is_superuser
        user.save()
        
        messages.success(request, f'User "{username}" created successfully!')
        return redirect('user_management:user_detail', pk=user.pk)
    
    return render(request, 'user_management/user_form.html', {'edit_mode': False})


@login_required
@user_passes_test(is_superuser)
def user_detail(request, pk):
    """View user details - superusers only"""
    user = get_object_or_404(User, pk=pk)
    
    context = {
        'view_user': user,
    }
    return render(request, 'user_management/user_detail.html', context)


@login_required
@user_passes_test(is_superuser)
def user_edit(request, pk):
    """Edit user - superusers only"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.is_staff = request.POST.get('is_staff') == 'on'
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        user.save()
        
        messages.success(request, f'User "{user.username}" updated successfully!')
        return redirect('user_management:user_detail', pk=user.pk)
    
    context = {
        'edit_mode': True,
        'edit_user': user,
    }
    return render(request, 'user_management/user_form.html', context)


@login_required
@user_passes_test(is_superuser)
def user_toggle_status(request, pk):
    """Activate/deactivate user - superusers only"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        user.is_active = not user.is_active
        user.save()
        
        status = "activated" if user.is_active else "deactivated"
        messages.success(request, f'User "{user.username}" {status}!')
    
    return redirect('user_management:user_detail', pk=pk)


@login_required
@user_passes_test(is_superuser)
def user_reset_password(request, pk):
    """Reset user password - superusers only"""
    user = get_object_or_404(User, pk=pk)
    
    if request.method == 'POST':
        new_password = request.POST.get('new_password')
        user.set_password(new_password)
        user.save()
        
        messages.success(request, f'Password reset for user "{user.username}"!')
        return redirect('user_management:user_detail', pk=pk)
    
    context = {
        'reset_user': user,
    }
    return render(request, 'user_management/reset_password.html', context)
