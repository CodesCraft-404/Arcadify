# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('create-superuser/', views.create_superuser),
    path('', views.login_register_view, name='login_register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
]