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
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import CustomUser, FriendRequest, Friendship

# ===== SEND FRIEND REQUEST =====
@login_required
@require_POST
def send_friend_request_ajax(request):
    user_id = request.POST.get('user_id')
    if not user_id:
        return JsonResponse({'error': 'User ID required'}, status=400)

    try:
        to_user = CustomUser.objects.get(id=int(user_id))
    except (CustomUser.DoesNotExist, ValueError):
        return JsonResponse({'error': 'User not found'}, status=404)

    if to_user == request.user:
        return JsonResponse({'error': 'Cannot send request to yourself'}, status=400)

    fr, created = FriendRequest.objects.get_or_create(
        from_user=request.user, to_user=to_user, defaults={'accepted': False}
    )
    if not created:
        return JsonResponse({'error': 'Request already sent'}, status=400)

    return JsonResponse({'success': f'Request sent to {to_user.gamer_name}'})


# ===== RESPOND TO FRIEND REQUEST =====
@login_required
@require_POST
def respond_friend_request_ajax(request):
    fr_id = request.POST.get('request_id')
    action = request.POST.get('action')

    if not fr_id or action not in ['accept', 'reject']:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)

    fr = get_object_or_404(FriendRequest, id=fr_id, to_user=request.user)

    if action == 'accept':
        fr.accepted = True
        fr.save()
        # create bidirectional friendship
        Friendship.objects.get_or_create(user1=fr.from_user, user2=fr.to_user)
        Friendship.objects.get_or_create(user1=fr.to_user, user2=fr.from_user)
        return JsonResponse({'success': f'You are now friends with {fr.from_user.gamer_name}'})
    else:  # reject
        fr.delete()
        return JsonResponse({'success': 'Friend request rejected'})


# ===== GET FRIENDS + PENDING REQUESTS (AJAX) =====
@login_required
def get_friends_ajax(request):
    try:
        user = request.user
        friends_qs = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friends = []
        for f in friends_qs:
            friend_user = f.user2 if f.user1 == user else f.user1
            # fallback if is_online missing
            online_status = getattr(friend_user, 'is_online', False)
            friends.append({
                'id': friend_user.id,
                'name': friend_user.gamer_name,
                'online': online_status
            })

        pending_qs = FriendRequest.objects.filter(to_user=user, accepted=False)
        pending_requests = [{'id': fr.id, 'name': fr.from_user.gamer_name} for fr in pending_qs]

        return JsonResponse({'friends': friends, 'pending_requests': pending_requests})
    except Exception as e:
        import traceback
        print("Error in get_friends_ajax:", e)
        traceback.print_exc()
        return JsonResponse({'friends': [], 'pending_requests': []})


# ===== SEARCH USERS (AJAX) =====
@login_required
def search_users_ajax(request):
    try:
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse({'results': []})

        user = request.user
        friends_qs = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friend_ids = set()
        for f in friends_qs:
            friend_ids.add(f.user1.id)
            friend_ids.add(f.user2.id)
        friend_ids.add(user.id)

        users = CustomUser.objects.filter(
            gamer_name__icontains=query
        ).exclude(id__in=friend_ids)[:5]

        results = [{'id': u.id, 'name': u.gamer_name} for u in users]
        return JsonResponse({'results': results})
    except Exception as e:
        import traceback
        print("Error in search_users_ajax:", e)
        traceback.print_exc()
        return JsonResponse({'results': []})


# ===== OPTIONAL: FRIENDS LIST PAGE (for template) =====
@login_required
def friends_list_view(request):
    user = request.user

    # Friends via FriendRequest (accepted=True)
    friends_qs = FriendRequest.objects.filter(
        Q(from_user=user) | Q(to_user=user), accepted=True
    )
    friends = []
    for fr in friends_qs:
        friend_user = fr.to_user if fr.from_user == user else fr.from_user
        friends.append({'name': friend_user.gamer_name, 'online': friend_user.is_online})

    # Pending friend requests
    pending_requests = FriendRequest.objects.filter(to_user=user, accepted=False)

    return render(request, 'accounts/friends.html', {
        'friends': friends,
        'pending_requests': pending_requests
    })