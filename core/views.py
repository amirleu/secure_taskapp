from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404
from django.core.exceptions import PermissionDenied
from .models import CustomUser, Task, AuditLog
from .forms import RegisterForm, LoginForm, TaskForm, ProfileUpdateForm
from .utils import log_audit, rename_uploaded_file
import logging

security_logger = logging.getLogger('security')


# ── Access Control Decorator ─────────────────────────────────────────────────

def admin_required(view_func):
    """Custom decorator: only allow admin users"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_admin_user():
            log_audit(request.user, 'access_denied',
                     f'Attempted to access admin view: {request.path}', request)
            security_logger.warning(
                f'Access denied: {request.user.username} tried {request.path}'
            )
            raise PermissionDenied  # Returns 403
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


# ── Auth Views ────────────────────────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            log_audit(user, 'login_success',
                     f'New user registered: {user.username}', request)
            messages.success(request, 'Account created. Please login.')
            return redirect('login')
        else:
            messages.error(request, 'Please fix the errors below.')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                log_audit(user, 'login_success',
                         f'User logged in: {username}', request)
                return redirect('dashboard')
            else:
                # Log failed attempt — note: we do NOT log the password
                log_audit(None, 'login_failed',
                         f'Failed login attempt for username: {username}', request)
                security_logger.warning(
                    f'Failed login: {username} from {request.META.get("REMOTE_ADDR")}'
                )
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid credentials.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


@login_required
def logout_view(request):
    if request.method == 'POST':  # Require POST for logout (CSRF protection)
        log_audit(request.user, 'logout',
                 f'User logged out: {request.user.username}', request)
        logout(request)
        return redirect('login')
    return redirect('dashboard')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard_view(request):
    if request.user.is_admin_user():
        # Admin sees all tasks
        tasks = Task.objects.all().select_related('assigned_to', 'created_by')
    else:
        # Normal user sees only their own tasks (prevents IDOR)
        tasks = Task.objects.filter(
            assigned_to=request.user
        ).select_related('assigned_to', 'created_by')

    context = {
        'tasks': tasks,
        'task_count': tasks.count(),
    }
    return render(request, 'dashboard.html', context)


# ── Task CRUD ─────────────────────────────────────────────────────────────────

@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.assigned_to = request.user

            # Rename uploaded file to UUID
            if task.attachment:
                task.attachment = rename_uploaded_file(task.attachment)

            task.save()
            log_audit(request.user, 'task_create',
                     f'Task created: {task.title[:50]}', request)
            messages.success(request, 'Task created successfully.')
            return redirect('dashboard')
    else:
        form = TaskForm()

    return render(request, 'tasks/create.html', {'form': form})


@login_required
def task_update(request, task_id):
    # Prevent IDOR: filter by both id AND owner (or admin)
    if request.user.is_admin_user():
        task = get_object_or_404(Task, id=task_id)
    else:
        task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, request.FILES, instance=task)
        if form.is_valid():
            updated_task = form.save(commit=False)

            if updated_task.attachment:
                updated_task.attachment = rename_uploaded_file(updated_task.attachment)

            updated_task.save()
            log_audit(request.user, 'task_update',
                     f'Task updated: {task.title[:50]}', request)
            messages.success(request, 'Task updated.')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)

    return render(request, 'tasks/update.html', {'form': form, 'task': task})


@login_required
def task_delete(request, task_id):
    # Prevent IDOR
    if request.user.is_admin_user():
        task = get_object_or_404(Task, id=task_id)
    else:
        task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    if request.method == 'POST':
        title = task.title
        task.delete()
        log_audit(request.user, 'task_delete',
                 f'Task deleted: {title[:50]}', request)
        messages.success(request, 'Task deleted.')
        return redirect('dashboard')

    return render(request, 'tasks/delete_confirm.html', {'task': task})


@login_required
def task_detail(request, task_id):
    # Prevent IDOR
    if request.user.is_admin_user():
        task = get_object_or_404(Task, id=task_id)
    else:
        task = get_object_or_404(Task, id=task_id, assigned_to=request.user)

    return render(request, 'tasks/detail.html', {'task': task})


# ── Profile ───────────────────────────────────────────────────────────────────

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'profile_update',
                     f'Profile updated for: {request.user.username}', request)
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)

    return render(request, 'profile.html', {'form': form})


# ── Audit Log (Admin Only) ────────────────────────────────────────────────────

@login_required
@admin_required
def audit_log_view(request):
    logs = AuditLog.objects.all().select_related('user')[:500]
    return render(request, 'admin/audit_log.html', {'logs': logs})


# ── Custom Error Handlers ─────────────────────────────────────────────────────

def error_400(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
