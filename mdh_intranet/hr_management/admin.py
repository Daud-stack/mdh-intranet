from django.contrib import admin
from .models import Attendance, PerformanceReview, TrainingRecord

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'clock_in', 'clock_out', 'location')
    list_filter = ('date', 'location')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(PerformanceReview)
class PerformanceReviewAdmin(admin.ModelAdmin):
    list_display = ('employee', 'reviewer', 'review_date', 'rating')
    list_filter = ('review_date', 'rating')
    search_fields = ('employee__username', 'reviewer__username')

@admin.register(TrainingRecord)
class TrainingRecordAdmin(admin.ModelAdmin):
    list_display = ('course_name', 'employee', 'completion_date', 'expiry_date')
    list_filter = ('completion_date',)
    search_fields = ('course_name', 'employee__username')

