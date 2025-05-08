from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from .views import home_view

urlpatterns = [
    path('', home_view, name='home'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('register/', views.register_view, name='register'),  # URL for the sign-up page


]
