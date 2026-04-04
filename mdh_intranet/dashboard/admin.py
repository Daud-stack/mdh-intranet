from django.contrib import admin
from .models import Announcement

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'severity', 'date_posted', 'is_active')
    list_filter = ('severity', 'is_active', 'date_posted')
    search_fields = ('title', 'content')
