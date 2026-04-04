from django.contrib import admin
from .models import Ticket, TicketComment

class CommentInline(admin.TabularInline):
    model = TicketComment
    extra = 0
    fields = ('author', 'text', 'created_at', 'is_internal')
    readonly_fields = ('created_at',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('title', 'requester', 'assignee', 'priority', 'status', 'created_at')
    list_filter = ('status', 'priority', 'category')
    search_fields = ('title', 'description', 'requester__username')
    inlines = [CommentInline]
    date_hierarchy = 'created_at'

@admin.register(TicketComment)
class TicketCommentAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'created_at', 'is_internal')
    search_fields = ('text',)
