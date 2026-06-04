import uuid
import os
import logging

security_logger = logging.getLogger('security')
app_logger = logging.getLogger('app')


def get_client_ip(request):
    """Get real IP address from request"""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def rename_uploaded_file(file, folder='uploads'):
    """Rename uploaded file to UUID to prevent path traversal"""
    ext = os.path.splitext(file.name)[1].lower()
    new_name = f"{uuid.uuid4()}{ext}"
    file.name = new_name
    return file


def log_audit(user, action, description, request=None):
    """
    Create an audit log entry.
    NEVER pass passwords, tokens, or sensitive data to description.
    """
    from .models import AuditLog

    ip = get_client_ip(request) if request else None
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:300] if request else ''

    AuditLog.objects.create(
        user=user if user and user.is_authenticated else None,
        action=action,
        description=description,  # Must not contain sensitive data
        ip_address=ip,
        user_agent=user_agent
    )
