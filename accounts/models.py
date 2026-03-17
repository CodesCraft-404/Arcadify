# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, gmail, password, **extra_fields):
        if not gmail:
            raise ValueError('The Email (gmail) must be set')
        gmail = self.normalize_email(gmail)
        user = self.model(gmail=gmail, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, gmail, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')

        return self.create_user(gmail, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    id = models.BigAutoField(primary_key=True)                # ID
    name = models.CharField(max_length=100)                   # Full name
    gamer_name = models.CharField(max_length=50, unique=True) # Gamer name
    age = models.PositiveIntegerField(null=True, blank=True) # Age
    gmail = models.EmailField(unique=True)                   # Email/login
    date_joined = models.DateTimeField(default=timezone.now) # Date joined
    last_login = models.DateTimeField(blank=True, null=True) # Last login
    is_superuser = models.BooleanField(default=False)        # Superuser
    is_staff = models.BooleanField(default=False)            # Staff/admin
    is_active = models.BooleanField(default=True)            # Active/banned
    last_seen = models.DateTimeField(blank=True, null=True)  # Last time user was active
    level = models.PositiveIntegerField(default=1)           # Level
    coins = models.IntegerField(default=0)                   # Coins

    USERNAME_FIELD = 'gmail'           # login with gmail
    REQUIRED_FIELDS = ['name', 'gamer_name'] # required for superuser creation

    objects = CustomUserManager()

    friends = models.ManyToManyField(
        "self",
        symmetrical=True,
        blank=True
    )

    def __str__(self):
        return self.gamer_name

    @property
    def is_online(self):
        """User is online if last_seen was within the last 15 seconds"""
        if not self.last_seen:
            return False
        return timezone.now() - self.last_seen < timedelta(seconds=15)

from django.conf import settings
from django.db import models

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_requests'
    )

    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_requests'
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')  # 🚀 prevents duplicate requests

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.status})"