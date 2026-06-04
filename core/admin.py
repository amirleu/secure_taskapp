from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Task, AuditLog


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('role', 'phone', 'profile_picture')}),
    )


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'assigned_to', 'priority', 'status', 'created_at']
    list_filter = ['priority', 'status']
    search_fields = ['title', 'description']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action', 'ip_address']
    list_filter = ['action']
    readonly_fields = ['user', 'action', 'description', 'ip_address', 'timestamp']
    # Read-only — audit logs must not be editable

    def has_add_permission(self, request):
        return False  # Cannot manually add audit logs

    def has_delete_permission(self, request, obj=None):
        return False  # Cannot delete audit logs
