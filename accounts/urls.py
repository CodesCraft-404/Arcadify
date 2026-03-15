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
    path('friend-request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/respond/<int:request_id>/<str:action>/', views.respond_friend_request, name='respond_friend_request'),
]