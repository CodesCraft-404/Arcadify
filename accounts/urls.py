# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_register_view, name='login_register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_page_view, name='admin_page'),
    path('search-players/', views.search_players, name='search_players'),
    path('send-request/', views.send_friend_request, name='send_friend_request'),
    path('accept-request/', views.accept_request),
    path('reject-request/', views.reject_request),
    path("refresh-friends/", views.refresh_friends, name="refresh_friends"),
    path("fix-friends/", views.fix_friends),
]