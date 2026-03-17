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

from django.db import IntegrityError

@login_required
def send_friend_request(request):
    if request.method == "POST":
        to_user_id = request.POST.get("user_id")

        if not to_user_id:
            return JsonResponse({"error": "Missing user_id"}, status=400)

        try:
            to_user = CustomUser.objects.get(id=to_user_id)
        except CustomUser.DoesNotExist:
            return JsonResponse({"error": "User not found"}, status=404)

        # 🚫 prevent sending to yourself
        if to_user == request.user:
            return JsonResponse({"error": "Cannot send request to yourself"}, status=400)

        # 🔥 CHECK REVERSE REQUEST (SMART LOGIC)
        reverse_request = FriendRequest.objects.filter(
            from_user=to_user,
            to_user=request.user,
            status='pending'
        ).first()

        if reverse_request:
            reverse_request.status = 'accepted'
            reverse_request.save()
            return JsonResponse({"success": True, "message": "Friend added!"})

        # ✅ CREATE REQUEST (SAFE)
        try:
            FriendRequest.objects.create(
                from_user=request.user,
                to_user=to_user
            )
            return JsonResponse({"success": True})

        except IntegrityError:
            return JsonResponse({"error": "Request already exists"}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=400)