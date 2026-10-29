from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils import timezone

from config.forms import add_bootstrap

from .models import User


def only_digits(text):
    return ''.join(c for c in text if c.isdigit())


class LoginForm(AuthenticationForm):
    username = forms.EmailField(label='Email')
    error_messages = {
        'invalid_login': 'Wrong email or password, or your account is not active. Contact admin.',
        'inactive': 'Your account is not active. Contact admin.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


class RegisterForm(forms.Form):
    university_id = forms.CharField(max_length=20)
    phone = forms.CharField(max_length=20)
    full_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)

    def clean(self):
        data = super().clean()
        if self.errors:
            return data
        if data['password'] != data['confirm_password']:
            raise forms.ValidationError('Passwords do not match.')
        user = User.objects.filter(university_id=data['university_id'].strip()).first()
        if (
            user is None
            or user.status != 'active'
            or user.phone != only_digits(data['phone'])
            or (user.email or '').lower() != data['email'].lower()
            or user.full_name.lower() != data['full_name'].strip().lower()
        ):
            raise forms.ValidationError("Your details don't match.")
        if user.registered_at is not None:
            raise forms.ValidationError('This account is already registered. Please login.')
        self.user = user
        return data

    def save(self):
        user = self.user
        user.set_password(self.cleaned_data['password'])
        user.registered_at = timezone.now()
        user.save()
        return user
