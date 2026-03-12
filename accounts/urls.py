# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("reset-admin/", views.reset_admin),
    path('', views.login_register_view, name='login_register'),
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),
]