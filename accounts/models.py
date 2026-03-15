# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

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
    name = models.CharField(max_length=100)                  # Full name
    gamer_name = models.CharField(max_length=50, unique=True) # Gamer name
    age = models.PositiveIntegerField(null=True, blank=True) # Age
    gmail = models.EmailField(unique=True)                   # Email/login
    date_joined = models.DateTimeField(default=timezone.now) # Date joined
    last_login = models.DateTimeField(blank=True, null=True) # Last login
    is_superuser = models.BooleanField(default=False)        # Superuser
    is_staff = models.BooleanField(default=False)            # Staff/admin
    is_active = models.BooleanField(default=True)            # Active/banned
    is_online = models.BooleanField(default=False)           # Online status
    level = models.PositiveIntegerField(default=1)           # Level
    coins = models.IntegerField(default=0)                   # Coins

    USERNAME_FIELD = 'gmail'           # login with gmail
    REQUIRED_FIELDS = ['name', 'gamer_name'] # required for superuser creation

    objects = CustomUserManager()

    def __str__(self):
        return self.gamer_name

# accounts/models.py (continuation)

class FriendRequest(models.Model):
    from_user = models.ForeignKey(
        CustomUser, 
        related_name='sent_requests', 
        on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        CustomUser, 
        related_name='received_requests', 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)  # True if accepted

    class Meta:
        unique_together = ('from_user', 'to_user')  # prevent duplicate requests

    def __str__(self):
        return f"{self.from_user.gamer_name} → {self.to_user.gamer_name} ({'Accepted' if self.accepted else 'Pending'})"


class Friendship(models.Model):
    user1 = models.ForeignKey(CustomUser, related_name='friendships_initiated', on_delete=models.CASCADE)
    user2 = models.ForeignKey(CustomUser, related_name='friendships_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')  # prevent duplicate friendships

    def save(self, *args, **kwargs):
        # enforce user1.id < user2.id to ensure uniqueness for bidirectional friendship
        if self.user1.id > self.user2.id:
            self.user1, self.user2 = self.user2, self.user1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user1.gamer_name} ↔ {self.user2.gamer_name}"