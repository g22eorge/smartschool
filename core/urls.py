from django.urls import path
from . import views
<<<<<<< HEAD
from .views_help import help_view
=======
from django.views.generic import RedirectView
>>>>>>> 821b5fb96f3e7a78459d76f33fbbe8c7be9c1045

app_name = 'core'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('help/', help_view, name='help'),
]
