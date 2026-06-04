from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .models import CustomUser, Task
import magic  # pip install python-magic
import os


# ── Validators ──────────────────────────────────────────────────────────────

username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_]{3,20}$',
    message='Username must be 3-20 characters. Letters, numbers, underscore only.'
)

phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message='Enter a valid phone number.'
)

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png']
ALLOWED_IMAGE_MIMES = ['image/jpeg', 'image/png']
ALLOWED_FILE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.pdf', '.txt']
ALLOWED_FILE_MIMES = ['image/jpeg', 'image/png', 'application/pdf', 'text/plain']
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB


def validate_image(file):
    """Validate profile picture uploads"""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(f'Only {", ".join(ALLOWED_IMAGE_EXTENSIONS)} files allowed.')
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError('File size must be under 5MB.')


def validate_attachment(file):
    """Validate task attachment uploads"""
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_FILE_EXTENSIONS:
        raise ValidationError(f'File type not allowed.')
    if file.size > MAX_UPLOAD_SIZE:
        raise ValidationError('File size must be under 5MB.')


# ── Forms ────────────────────────────────────────────────────────────────────

class RegisterForm(UserCreationForm):
    """User registration form with full validation"""
    username = forms.CharField(
        validators=[username_validator],
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'Email'})
    )
    phone = forms.CharField(
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={'placeholder': 'Phone (optional)'})
    )

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Extra XSS prevention - strip HTML characters
        if any(c in username for c in ['<', '>', '"', "'"]):
            raise ValidationError('Username contains invalid characters.')
        return username


class LoginForm(AuthenticationForm):
    """Login form"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class TaskForm(forms.ModelForm):
    """Task creation/edit form"""
    attachment = forms.FileField(
        required=False,
        validators=[validate_attachment]
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'priority', 'status', 'attachment']

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 3:
            raise ValidationError('Title must be at least 3 characters.')
        if len(title) > 200:
            raise ValidationError('Title too long.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) > 2000:
            raise ValidationError('Description too long (max 2000 chars).')
        return description


class ProfileUpdateForm(forms.ModelForm):
    """Profile update form"""
    profile_picture = forms.ImageField(
        required=False,
        validators=[validate_image]
    )

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Allow same email for current user but reject duplicates
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('This email is already used by another account.')
        return email
