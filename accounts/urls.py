# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_register_view, name='login_register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
    path('admin-panel/', views.admin_page_view, name='admin_page'),

    # Friends system
    path('friends/', views.friends_list_view, name='friends_list'),
    path('friends/ajax/', views.get_friends_ajax, name='get_friends_ajax'),
    path('friends/send/', views.send_friend_request_ajax, name='send_friend_request_ajax'),
    path('friends/respond/', views.respond_friend_request_ajax, name='respond_friend_request_ajax'),
    path('friends/search/', views.search_users_ajax, name='search_users_ajax'),
]