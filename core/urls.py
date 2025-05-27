from django.urls import path
from django.views.generic import RedirectView
from . import views
from .views_help import help_view

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('help/', help_view, name='help'),
]
