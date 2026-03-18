# accounts/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
import os
from django.conf import settings
from django.views.decorators.http import require_POST

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

                user.is_online = True
                user.save(update_fields=['is_online'])

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

    friends = request.user.friends.all()

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
        'pending_requests': pending_requests,
        'friends': friends   # 🔥 THIS LINE
    })


def logout_view(request):
    if request.user.is_authenticated:
        # ✅ Mark offline before logging out
        request.user.is_online = False
        request.user.save(update_fields=['is_online'])
        
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
from .models import CustomUser, FriendRequest
from django.db.models import Q

@login_required
def search_players(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    user = request.user

    # Exclude yourself and already friends
    accepted_requests = FriendRequest.objects.filter(
        Q(from_user=user) | Q(to_user=user),
        status='accepted'
    )

    friend_ids = set()
    for fr in accepted_requests:
        friend_ids.add(fr.from_user.id)
        friend_ids.add(fr.to_user.id)

    users = CustomUser.objects.filter(
        gamer_name__icontains=query
    ).exclude(id=user.id).exclude(id__in=friend_ids)[:10]

    data = [{"id": u.id, "gamer_name": u.gamer_name} for u in users]
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import CustomUser, FriendRequest
from django.db.models import Q

@login_required
def send_friend_request(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    to_username = request.POST.get("username")
    if not to_username:
        return JsonResponse({"error": "Missing username"}, status=400)

    try:
        to_user = CustomUser.objects.get(gamer_name=to_username)
    except CustomUser.DoesNotExist:
        return JsonResponse({"status": "invalid_user"}, status=404)

    if to_user == request.user:
        return JsonResponse({"status": "self_request"})

    # Check if already friends
    if FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=to_user, status='accepted') |
        Q(from_user=to_user, to_user=request.user, status='accepted')
    ).exists():
        return JsonResponse({"status": "already_friend", "name": to_user.gamer_name})

    # Already sent pending request
    if FriendRequest.objects.filter(
        from_user=request.user, to_user=to_user, status='pending'
    ).exists():
        return JsonResponse({"status": "already_sent", "name": to_user.gamer_name})

    # Reverse pending request → auto-accept
    reverse_request = FriendRequest.objects.filter(
        from_user=to_user, to_user=request.user, status='pending'
    ).first()

    if reverse_request:
        reverse_request.status = 'accepted'
        reverse_request.save()

        request.user.friends.add(to_user)
        to_user.friends.add(request.user)
        # ✅ Ensure both users are synced in the backend
        # No frontend polling needed, database is the source of truth
        return JsonResponse({
            "success": True,
            "message": f"You are now friends with {to_user.gamer_name}!",
            "friend_added": True,
            "friend_name": to_user.gamer_name,
            "friend_online": to_user.is_online
        })

    # Create a new request
    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    return JsonResponse({"success": True, "message": f"Friend request sent to {to_user.gamer_name}!"})

@require_POST
@login_required
def accept_request(request):
    req_id = request.POST.get("request_id")

    try:
        fr = FriendRequest.objects.get(id=req_id, to_user=request.user)
    except FriendRequest.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)

    # ✅ add both users as friends
    request.user.friends.add(fr.from_user)

    # ✅ update status
    fr.status = "accepted"
    fr.save()

    return JsonResponse({
        "success": True,
        "name": fr.from_user.gamer_name,
        "online": fr.from_user.is_online
    })

@require_POST
@login_required
def reject_request(request):
    req_id = request.POST.get("request_id")

    try:
        fr = FriendRequest.objects.get(id=req_id, to_user=request.user)
    except FriendRequest.DoesNotExist:
        return JsonResponse({"error": "Request not found"}, status=404)

    fr.status = "rejected"
    fr.delete()  # ✅ allow re-send later

    return JsonResponse({"success": True})

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import CustomUser, FriendRequest

@login_required
def refresh_friends(request):
    user = request.user

    # Friends
    friends = [
        {"gamer_name": f.gamer_name, "is_online": f.is_online}
        for f in user.friends.all()
    ]

    # Pending requests
    pending_requests = [
        {"id": fr.id, "from_user": fr.from_user.gamer_name}
        for fr in FriendRequest.objects.filter(to_user=user, status="pending")
    ]

    return JsonResponse({"friends": friends, "pending_requests": pending_requests})

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from .models import CustomUser

@login_required
def fix_friends(request):
    count = 0

    for user in CustomUser.objects.all():
        for friend in user.friends.all():
            if user not in friend.friends.all():
                friend.friends.add(user)
                count += 1

    return HttpResponse(f"✅ Fixed {count} friendships")