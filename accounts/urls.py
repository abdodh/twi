from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('profile/<str:username>/', views.profile_view, name='profile_with_username'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/profile/', views.profile_settings, name='profile_settings'),
    path('settings/account/', views.account_settings, name='account_settings'),
    path('settings/security/', views.security_settings, name='security_settings'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
