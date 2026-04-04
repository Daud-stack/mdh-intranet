from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Project
from .forms import ProjectForm

@login_required
def index(request):
    """Projects - Organizational project tracking"""
    projects = Project.objects.all()
    
    # Calculate stats
    active_projects = projects.filter(status='Active').count()
    completed_projects = projects.filter(status='Completed').count()
    on_hold_projects = projects.filter(status='On Hold').count()
    
    # Simple count of unique members across all projects
    # This is a basic approximation for stats
    total_members = set()
    for proj in projects:
        total_members.add(proj.manager.id)
        for member in proj.members.all():
            total_members.add(member.id)
            
    context = {
        'projects': projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'on_hold_projects': on_hold_projects,
        'total_members': len(total_members),
    }
    return render(request, 'projects/index.html', context)

@login_required
def project_create(request):
    """Create a new project"""
    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.manager = request.user
            project.save()
            form.save_m2m() # Save many-to-many data
            messages.success(request, f'Project "{project.title}" created successfully!')
            return redirect('projects:index')
    else:
        form = ProjectForm()
    
    context = {
        'form': form,
        'title': 'Create New Project'
    }
    return render(request, 'projects/project_form.html', context)

@login_required
def project_detail(request, pk):
    """View project details"""
    project = get_object_or_404(Project, pk=pk)
    context = {
        'project': project
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def project_update(request, pk):
    """Update an existing project"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions (only manager or superuser can edit)
    if project.manager != request.user and not request.user.is_superuser:
        messages.error(request, "You don't have permission to edit this project.")
        return redirect('projects:detail', pk=pk)

    if request.method == 'POST':
        form = ProjectForm(request.POST, request.FILES, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, f'Project "{project.title}" updated successfully!')
            return redirect('projects:detail', pk=pk)
    else:
        form = ProjectForm(instance=project)
    
    context = {
        'form': form,
        'title': f'Edit Project: {project.title}',
        'project': project
    }
    return render(request, 'projects/project_form.html', context)
