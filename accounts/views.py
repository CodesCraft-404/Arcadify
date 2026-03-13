# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser

def login_register_view(request):
    if request.method == 'POST':
        if 'login' in request.POST:
            gamer_name = request.POST['gamer_name']
            password = request.POST['password']
            try:
                user_obj = CustomUser.objects.get(gamer_name=gamer_name)
            except CustomUser.DoesNotExist:
                messages.error(request, 'Gamer name not found!')
                return render(request, 'accounts/login_registration.html')
            
            user = authenticate(request, gmail=user_obj.gmail, password=password)
            if user is not None:
                login(request, user)

                # check if superuser
                if user.is_superuser:
                    return redirect('admin_page')

                return redirect('home')
            else:
                messages.error(request, 'Incorrect password!')
                return render(request, 'accounts/login_registration.html')

        elif 'register' in request.POST:
            name = request.POST['name']
            gamer_name = request.POST['gamer_name']
            age = request.POST['age']
            gmail = request.POST['gmail']
            password = request.POST['password']
            confirm_password = request.POST['confirm_password']

            if password != confirm_password:
                messages.error(request, 'Passwords do not match!')
                return render(request, 'accounts/login_registration.html')

            if CustomUser.objects.filter(gamer_name=gamer_name).exists():
                messages.error(request, 'Gamer name already exists!')
                return render(request, 'accounts/login_registration.html')

            if CustomUser.objects.filter(gmail=gmail).exists():
                messages.error(request, 'Email already registered!')
                return render(request, 'accounts/login_registration.html')

            user = CustomUser.objects.create_user(
                gmail=gmail, password=password, name=name, gamer_name=gamer_name, age=age
            )
            login(request, user)
            return redirect('home')

    return render(request, 'accounts/login_registration.html')


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login_register')
    return render(request, 'accounts/home.html')


def logout_view(request):
    logout(request)
    return redirect('login_register')

def admin_page_view(request):

    if not request.user.is_authenticated:
        return redirect('login_register')

    if not request.user.is_superuser:
        return redirect('home')

    return render(request, 'accounts/admin.html')

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(gmail="admin@gmail.com").exists():
    User.objects.create_superuser(
        gmail="admin@gmail.com",
        name="Admin",
        gamer_name="admin",
        age=21,
        password="admin123"
    )