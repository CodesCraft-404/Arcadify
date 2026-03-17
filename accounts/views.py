# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
import os
from django.conf import settings

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


from .models import FriendRequest  # make sure this is imported

def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login_register')

    # ✅ Friend requests
    pending_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    )

    # ✅ Characters logic
    characters_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'characters')
    characters = []

    if os.path.exists(characters_dir):
        for char_folder in os.listdir(characters_dir):
            char_path = os.path.join(characters_dir, char_folder)

            if os.path.isdir(char_path):
                main_img = f'images/characters/{char_folder}/{char_folder}.png'

                skin_path = os.path.join(char_path, 'skin')
                skins = []
                if os.path.exists(skin_path):
                    skins = [
                        f'images/characters/{char_folder}/skin/{f}'
                        for f in sorted(os.listdir(skin_path)) if f.endswith('.png')
                    ]

                data_path = os.path.join(char_path, 'data')
                char_info = ''
                char_ability = ''

                if os.path.exists(data_path):
                    info_file = os.path.join(data_path, 'info.txt')
                    ability_file = os.path.join(data_path, 'ability.txt')

                    if os.path.exists(info_file):
                        with open(info_file, 'r', encoding='utf-8') as f:
                            char_info = f.read().strip()

                    if os.path.exists(ability_file):
                        with open(ability_file, 'r', encoding='utf-8') as f:
                            char_ability = f.read().strip()

                characters.append({
                    'name': char_folder,
                    'main_image': main_img,
                    'skins': skins,
                    'info': char_info,
                    'ability': char_ability,
                })

    # ✅ FINAL render (only once!)
    return render(request, 'accounts/home.html', {
        'characters': characters,
        'pending_requests': pending_requests
    })


def logout_view(request):
    logout(request)
    return redirect('login_register')

def admin_page_view(request):

    if not request.user.is_authenticated:
        return redirect('login_register')

    if not request.user.is_superuser:
        return redirect('home')

    return render(request, 'accounts/admin.html')

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import CustomUser

@login_required
def search_players(request):
    query = request.GET.get('q', '').strip()

    if query:
        users = CustomUser.objects.filter(
            gamer_name__icontains=query
        ).exclude(
            id=request.user.id   # 🚀 exclude yourself
        )[:10]

        data = [
            {
                "id": user.id,
                "gamer_name": user.gamer_name
            }
            for user in users
        ]
    else:
        data = []

    return JsonResponse(data, safe=False)

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