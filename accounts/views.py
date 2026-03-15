# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
from django.contrib.auth.decorators import login_required 
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


def home_view(request):
    if not request.user.is_authenticated:
        return redirect('login_register')

    # Path to characters folder (project-level static)
    characters_dir = os.path.join(settings.BASE_DIR, 'static', 'images', 'characters')

    characters = []

    if os.path.exists(characters_dir):
        for char_folder in os.listdir(characters_dir):
            char_path = os.path.join(characters_dir, char_folder)
            if os.path.isdir(char_path):
                # Main image
                main_img = f'images/characters/{char_folder}/{char_folder}.png'

                # Skins
                skin_path = os.path.join(char_path, 'skin')
                skins = []
                if os.path.exists(skin_path):
                    skins = [
                        f'images/characters/{char_folder}/skin/{f}'
                        for f in sorted(os.listdir(skin_path)) if f.endswith('.png')
                    ]

                # Data files
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

                # Append character data
                characters.append({
                    'name': char_folder,
                    'main_image': main_img,
                    'skins': skins,
                    'info': char_info,
                    'ability': char_ability,
                })

    return render(request, 'accounts/home.html', {'characters': characters})


def logout_view(request):
    logout(request)
    return redirect('login_register')

def admin_page_view(request):

    if not request.user.is_authenticated:
        return redirect('login_register')

    if not request.user.is_superuser:
        return redirect('home')

    return render(request, 'accounts/admin.html')

# accounts/views.py (friends section)
from django.shortcuts import get_object_or_404
from .models import CustomUser, FriendRequest, Friendship
from django.http import JsonResponse

def send_friend_request(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    to_user = get_object_or_404(CustomUser, id=user_id)

    # Prevent sending to self
    if request.user == to_user:
        return JsonResponse({'error': 'Cannot send request to yourself'}, status=400)

    # Check if request already exists
    fr, created = FriendRequest.objects.get_or_create(from_user=request.user, to_user=to_user)
    if not created:
        return JsonResponse({'error': 'Request already sent'}, status=400)

    return JsonResponse({'success': f'Request sent to {to_user.gamer_name}'})


def respond_friend_request(request, request_id, action):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required'}, status=403)

    fr = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)

    if action == 'accept':
        fr.accepted = True
        fr.save()

        # Create friendship (user1 <-> user2)
        Friendship.objects.get_or_create(user1=fr.from_user, user2=fr.to_user)
        Friendship.objects.get_or_create(user1=fr.to_user, user2=fr.from_user)

        return JsonResponse({'success': f'You are now friends with {fr.from_user.gamer_name}'})

    elif action == 'reject':
        fr.delete()
        return JsonResponse({'success': 'Friend request rejected'})

    else:
        return JsonResponse({'error': 'Invalid action'}, status=400)


@login_required
def friends_list_view(request):
    user = request.user

    # Friends = accepted requests where user is from_user or to_user
    friends_qs = FriendRequest.objects.filter(
        (models.Q(from_user=user) | models.Q(to_user=user)) & models.Q(accepted=True)
    )

    friends = []
    for fr in friends_qs:
        friend_user = fr.to_user if fr.from_user == user else fr.from_user
        friends.append({
            'name': friend_user.gamer_name,
            'online': friend_user.is_online
        })

    # Pending friend requests received by the user
    pending_requests = FriendRequest.objects.filter(to_user=user, accepted__isnull=True)

    return render(request, 'accounts/friends.html', {
        'friends': friends,
        'pending_requests': pending_requests
    })