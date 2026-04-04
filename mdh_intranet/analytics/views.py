import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

from mdh_intranet.incident_log.models import Incident
from mdh_intranet.capa.models import CAPARecord
from mdh_intranet.medical_aid.models import PreauthorizationRequest
from mdh_intranet.sop_manual.models import SOP
from mdh_intranet.stock_management.models import StockItem
from mdh_intranet.documents.models import Document
from mdh_intranet.helpdesk.models import Ticket
from mdh_intranet.projects.models import Project
from mdh_intranet.leave_management.models import LeaveRequest
from mdh_intranet.core.models import AuditLog, Notification, ApprovalWorkflow, ApprovalStep, SOPAcknowledgement
from mdh_intranet.clinical.models import Patient, Consultation, LabRequest, ImagingRequest, TheatreBooking

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def dashboard(request):
    """Centralized Analytics & Reporting Engine."""
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # ── Incidents Activity ──
    try:
        incidents = Incident.objects.all()
        inc_open = incidents.filter(status__in=['New', 'Under Investigation', 'Open']).count()
        inc_high = incidents.filter(severity__in=['High', 'Critical']).count()
        inc_total = incidents.count()
        incidents_this_month = incidents.filter(created_at__gte=thirty_days_ago).count()
    except Exception:
        inc_open = inc_high = inc_total = incidents_this_month = 0

    # ── CAPA Metrics ──
    try:
        capas = CAPARecord.objects.all()
        capa_open = capas.exclude(status__in=['closed', 'cancelled']).count()
        capa_overdue = capas.filter(target_completion_date__lt=now.date()).exclude(status__in=['closed', 'cancelled']).count()
        closed_capas_month = capas.filter(status='closed', closed_at__gte=thirty_days_ago).count()
        total_capas = capas.count()
    except Exception:
        capa_open = capa_overdue = closed_capas_month = total_capas = 0

    # ── Medical Aid Metrics ──
    try:
        preauths = PreauthorizationRequest.objects.all()
        pa_pending = preauths.filter(status='PENDING').count()
        pa_approved = preauths.filter(status='APPROVED').count()
        pa_rejected = preauths.filter(status='REJECTED').count()
        
        pa_counts = preauths.values('status').annotate(count=Count('id')).order_by('status')
        try:
            pa_choices = dict(PreauthorizationRequest.STATUS_CHOICES)
        except AttributeError:
            pa_choices = {}
        chart_pa_labels = [str(pa_choices.get(c['status'], c['status'])) for c in pa_counts]
        chart_pa_data = [c['count'] for c in pa_counts]
    except Exception:
        pa_pending = pa_approved = pa_rejected = 0
        chart_pa_labels = chart_pa_data = []

    # ── SOPs & Compliance ──
    try:
        sops = SOP.objects.all()
        total_sops = sops.count()
        sop_published = sops.filter(status='Published').count()
        sop_outdated = sops.filter(status='Review Needed').count()

        total_acks = SOPAcknowledgement.objects.count()
        total_staff = User.objects.filter(is_active=True).count()
    except Exception:
        total_sops = sop_published = sop_outdated = total_acks = total_staff = 0

    # ── Stock Monitoring ──
    try:
        from django.db.models import F
        stock_total = StockItem.objects.count()
        low_stock_items = StockItem.objects.filter(current_quantity__lte=F('minimum_quantity')).count()
    except Exception:
        stock_total = low_stock_items = 0

    # ── Helpdesk Stats ──
    try:
        total_tickets = Ticket.objects.count()
        open_tickets = Ticket.objects.filter(status='open').count()
        tickets_this_month = Ticket.objects.filter(created_at__gte=thirty_days_ago).count()
    except Exception:
        total_tickets = open_tickets = tickets_this_month = 0

    # ── Clinical Operations ──
    try:
        total_patients = Patient.objects.count()
        cons_this_month = Consultation.objects.filter(date__gte=thirty_days_ago).count()
        lab_active = LabRequest.objects.exclude(status='completed').count()
        img_active = ImagingRequest.objects.exclude(status='completed').count()
        theatre_today = TheatreBooking.objects.filter(proposed_date__date=now.date()).count()
        
        # Clinical charts
        daily_consultations = []
        for d in range(6, -1, -1):
            day = now.date() - timedelta(days=d)
            daily_consultations.append(Consultation.objects.filter(date__date=day).count())
    except Exception:
        total_patients = cons_this_month = lab_active = img_active = theatre_today = 0
        daily_consultations = [0]*7

    # ── Document Stats ──
    try:
        total_docs = Document.objects.count()
    except Exception:
        total_docs = 0

    # ── Leave Stats ──
    try:
        total_leave = LeaveRequest.objects.count()
        pending_leave = LeaveRequest.objects.filter(status='PENDING').count()
    except Exception:
        total_leave = pending_leave = 0

    # ── Approval Stats ──
    try:
        total_workflows = ApprovalWorkflow.objects.count()
        pending_workflows = ApprovalWorkflow.objects.filter(status='pending').count()
        approved_workflows = ApprovalWorkflow.objects.filter(status='approved').count()
    except Exception:
        total_workflows = pending_workflows = approved_workflows = 0

    # ── Audit & Activity Stats ──
    try:
        audit_today = AuditLog.objects.filter(timestamp__date=now.date()).count()
        audit_week = AuditLog.objects.filter(timestamp__gte=seven_days_ago).count()
        top_active_users = list(
            AuditLog.objects.filter(timestamp__gte=thirty_days_ago)
            .values('user__username')
            .annotate(action_count=Count('id'))
            .order_by('-action_count')[:10]
        )
    except Exception:
        audit_today = audit_week = 0
        top_active_users = []

    # ── Fleet Metrics ──
    try:
        from mdh_intranet.fleet_management.models import Vehicle
        total_vehicles = Vehicle.objects.count()
        available_vehicles = Vehicle.objects.filter(status='AVAILABLE').count()
    except Exception:
        total_vehicles = available_vehicles = 0

    # ── Maintenance Metrics ──
    try:
        from mdh_intranet.maintenance.models import WorkOrder
        total_work_orders = WorkOrder.objects.count()
        open_work_orders = WorkOrder.objects.filter(status__in=['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'ON_HOLD']).count()
        wo_counts = WorkOrder.objects.values('status').annotate(count=Count('id')).order_by('status')
        wo_choices = dict(WorkOrder.STATUS_CHOICES)
        chart_wo_labels = [str(wo_choices.get(c['status'], c['status'])) for c in wo_counts]
        chart_wo_data = [c['count'] for c in wo_counts]
    except Exception:
        open_work_orders = total_work_orders = 0
        chart_wo_labels = chart_wo_data = []

    # ── HR Metrics ──
    try:
        from mdh_intranet.hr_management.models import HiringRequest
        pending_hiring = HiringRequest.objects.filter(status='PENDING').count()
    except Exception:
        pending_hiring = 0

    # ── Quality Audits ──
    try:
        from mdh_intranet.quality_audit.models import AuditSubmission
        completed_audits_month = AuditSubmission.objects.filter(conducted_at__gte=thirty_days_ago).count()
        total_audits = AuditSubmission.objects.count()
    except Exception:
        completed_audits_month = total_audits = 0

    # ── Chart Data Aggregations ──
    try:
        cat_counts = incidents.values('category').annotate(count=Count('id')).order_by('-count')
        cat_choices = dict(Incident.CATEGORY_CHOICES)
        chart_inc_cat_labels = [str(cat_choices.get(c['category'], c['category'])) for c in cat_counts]
        chart_inc_cat_data = [c['count'] for c in cat_counts]
        
        sev_counts = incidents.values('severity').annotate(count=Count('id')).order_by('-count')
        sev_choices = dict(Incident.SEVERITY_CHOICES)
        chart_inc_sev_labels = [str(sev_choices.get(c['severity'], c['severity'])) for c in sev_counts]
        chart_inc_sev_data = [c['count'] for c in sev_counts]
    except Exception:
        chart_inc_cat_labels = chart_inc_cat_data = chart_inc_sev_labels = chart_inc_sev_data = []

    try:
        stat_counts = capas.values('status').annotate(count=Count('id')).order_by('status')
        stat_choices = dict(CAPARecord.STATUS_CHOICES)
        chart_capa_labels = [str(stat_choices.get(c['status'], c['status'])) for c in stat_counts]
        chart_capa_data = [c['count'] for c in stat_counts]
    except Exception:
        chart_capa_labels = chart_capa_data = []

    try:
        sops_by_category = list(
            SOP.objects.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )
        chart_sop_cat_labels = [str(c['category__name'] or 'Uncategorized') for c in sops_by_category]
        chart_sop_cat_data = [c['count'] for c in sops_by_category]
    except Exception:
        chart_sop_cat_labels = chart_sop_cat_data = []

    # ── Trend data (last 7 days) ──
    daily_incidents = [0] * 7
    daily_tickets = [0] * 7
    daily_audits = [0] * 7
    labels = []
    
    try:
        # Build labels from 6 days ago -> today
        for i in range(6, -1, -1):
            day = (now - timedelta(days=i)).date()
            labels.append(day.strftime('%a'))

        # DB level grouping to prevent 21 separate count queries
        seven_days_start = (now - timedelta(days=6)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        from django.db.models.functions import TruncDate

        inc_trend = Incident.objects.filter(created_at__gte=seven_days_start)\
            .annotate(date=TruncDate('created_at'))\
            .values('date').annotate(c=Count('id'))
            
        tkt_trend = Ticket.objects.filter(created_at__gte=seven_days_start)\
            .annotate(date=TruncDate('created_at'))\
            .values('date').annotate(c=Count('id'))
            
        aud_trend = AuditLog.objects.filter(timestamp__gte=seven_days_start)\
            .annotate(date=TruncDate('timestamp'))\
            .values('date').annotate(c=Count('id'))

        # Map back to array indexes
        date_list = [(now - timedelta(days=i)).date() for i in range(6, -1, -1)]
        
        for item in inc_trend:
            if item['date'] in date_list:
                daily_incidents[date_list.index(item['date'])] = item['c']
                
        for item in tkt_trend:
            if item['date'] in date_list:
                daily_tickets[date_list.index(item['date'])] = item['c']
                
        for item in aud_trend:
            if item['date'] in date_list:
                daily_audits[date_list.index(item['date'])] = item['c']
                
    except Exception as e:
        print(e)
        pass

    context = {
        'inc_total': inc_total,
        'inc_open': inc_open,
        'inc_high': inc_high,
        'incidents_this_month': incidents_this_month,
        
        'capa_open': capa_open,
        'capa_overdue': capa_overdue,
        'total_capas': total_capas,
        'closed_capas_month': closed_capas_month,
        
        'pa_pending': pa_pending,
        'pa_approved': pa_approved,
        'pa_rejected': pa_rejected,
        
        'total_sops': total_sops,
        'sop_published': sop_published,
        'sop_outdated': sop_outdated,
        'total_acks': total_acks,
        'total_staff': total_staff,
        
        'stock_total': stock_total,
        'low_stock': low_stock_items,

        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'tickets_this_month': tickets_this_month,

        'total_docs': total_docs,
        
        # Clinical
        'total_patients': total_patients,
        'consultations_month': cons_this_month,
        'lab_active': lab_active,
        'img_active': img_active,
        'theatre_today': theatre_today,
        'daily_consultations': json.dumps(daily_consultations),
        
        'total_leave': total_leave,
        'pending_leave': pending_leave,

        'total_workflows': total_workflows,
        'pending_workflows': pending_workflows,
        'approved_workflows': approved_workflows,

        'audit_today': audit_today,
        'audit_week': audit_week,
        'top_active_users': top_active_users,
        
        'chart_inc_cat_labels': json.dumps(chart_inc_cat_labels),
        'chart_inc_cat_data': json.dumps(chart_inc_cat_data),
        'chart_inc_sev_labels': json.dumps(chart_inc_sev_labels),
        'chart_inc_sev_data': json.dumps(chart_inc_sev_data),
        
        'chart_capa_labels': json.dumps(chart_capa_labels),
        'chart_capa_data': json.dumps(chart_capa_data),

        'chart_sop_cat_labels': json.dumps(chart_sop_cat_labels),
        'chart_sop_cat_data': json.dumps(chart_sop_cat_data),

        'chart_trend_labels': json.dumps(labels),
        'daily_incidents': json.dumps(daily_incidents),
        'daily_tickets': json.dumps(daily_tickets),
        'daily_audits': json.dumps(daily_audits),

        'chart_top_users_labels': json.dumps([str(u['user__username'] or 'Unknown') for u in top_active_users]),
        'chart_top_users_data': json.dumps([u['action_count'] for u in top_active_users]),
        
        # New Context Variables
        'total_vehicles': total_vehicles,
        'available_vehicles': available_vehicles,
        'total_work_orders': total_work_orders,
        'open_work_orders': open_work_orders,
        'pending_hiring': pending_hiring,
        'completed_audits_month': completed_audits_month,
        'total_audits': total_audits,
        
        'chart_wo_labels': json.dumps(chart_wo_labels),
        'chart_wo_data': json.dumps(chart_wo_data),
        'chart_pa_labels': json.dumps(chart_pa_labels),
        'chart_pa_data': json.dumps(chart_pa_data),
    }
    
    return render(request, 'analytics/dashboard.html', context)
