from django.contrib import admin
from .models import TrainingCourse, Certification

@admin.register(TrainingCourse)
class TrainingCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_mandatory', 'validity_months', 'provider', 'created_at')
    list_filter = ('is_mandatory',)
    search_fields = ('title', 'description', 'provider')

@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = ('employee', 'course', 'date_completed', 'expiry_date')
    list_filter = ('course', 'date_completed')
    search_fields = ('employee__username', 'course__title')
