from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib import messages
from .models import Ticket, TicketComment
from .forms import TicketForm, TicketUpdateForm, CommentForm

def is_helpdesk_agent(user):
    return user.is_staff or user.groups.filter(name='IT Helpdesk').exists()

@login_required
def index(request):
    """List all tickets for the user or everyone (staff/agents)."""
    is_agent = is_helpdesk_agent(request.user)
    
    # For staff/agents, default to all tickets; for regular users, default to their tickets
    if is_agent:
        tickets = Ticket.objects.all().order_by('-created_at')
    else:
        tickets = Ticket.objects.filter(requester=request.user).order_by('-created_at')

    # Basic filtering logic can be added here
    status = request.GET.get('status')
    if status == 'open':
        tickets = tickets.filter(status='open')
    elif status == 'resolved':
        tickets = tickets.filter(status__in=['resolved', 'closed'])

    context = {
        'tickets': tickets,
        'open_count': tickets.filter(status='open').count(),
        'resolved_count': tickets.filter(status__in=['resolved', 'closed']).count(),
        'is_agent': is_agent,
    }
    return render(request, 'helpdesk/ticket_list.html', context)

@login_required
def create_ticket(request):
    """Create a new helpdesk ticket."""
    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.requester = request.user
            ticket.save()
            messages.success(request, f'Ticket {ticket.ticket_id} created successfully.')
            return redirect('helpdesk:detail', pk=ticket.pk)
    else:
        form = TicketForm()

    return render(request, 'helpdesk/ticket_form.html', {'form': form})

@login_required
def ticket_detail(request, pk):
    """View ticket details and handle comments."""
    ticket = get_object_or_404(Ticket, pk=pk)
    is_agent = is_helpdesk_agent(request.user)
    
    # Permission check: ensure user is staff/agent, requester, or assignee
    if not (is_agent or request.user == ticket.requester or request.user == ticket.assignee):
        messages.error(request, "Access denied.")
        return redirect('helpdesk:index')

    comment_form = CommentForm()

    if request.method == "POST":
        # Check if staff/agent update form was submitted
        if 'update_ticket' in request.POST and is_agent:
            update_form = TicketUpdateForm(request.POST, instance=ticket)
            if update_form.is_valid():
                update_form.save()
                messages.success(request, "Ticket updated.")
                return redirect('helpdesk:detail', pk=pk)
        
        # Check if staff/agent claimed the ticket
        elif 'claim_ticket' in request.POST and is_agent:
            ticket.assignee = request.user
            if ticket.status == 'open':
                ticket.status = 'in_progress'
            ticket.save()
            messages.success(request, "Ticket assigned to you.")
            return redirect('helpdesk:detail', pk=pk)
        
        # Check if comment form was submitted
        elif 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = request.user
                comment.save()
                messages.success(request, "Comment added.")
                return redirect('helpdesk:detail', pk=pk)

    update_form = TicketUpdateForm(instance=ticket) if is_agent else None

    context = {
        'ticket': ticket,
        'comments': ticket.comments.all().order_by('created_at'),
        'comment_form': comment_form,
        'update_form': update_form,
        'is_agent': is_agent,
    }
    return render(request, 'helpdesk/ticket_detail.html', context)
