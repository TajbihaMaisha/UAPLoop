from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class UserManager(BaseUserManager):
    def create_superuser(self, email, password):
        user = self.model(email=self.normalize_email(email), is_staff=True, is_superuser=True)
        user.set_password(password)
        user.save()
        return user


class User(AbstractBaseUser, PermissionsMixin):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    ]

    full_name = models.CharField(max_length=150, blank=True)
    university_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    email = models.EmailField(unique=True, null=True, blank=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = ''.join(c for c in self.phone if c.isdigit())
        self.is_active = self.status == 'active'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name or self.email or 'User'
