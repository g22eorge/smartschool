from django.urls import path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

app_name = 'users'

urlpatterns = [
    # User profile
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileUpdateView.as_view(), name='profile_edit'),
    
    # Password change
    path(
        'password/change/',
        auth_views.PasswordChangeView.as_view(
            template_name='account/password_change.html',
            success_url='/users/password/change/done/'
        ),
        name='account_change_password'
    ),
    path(
        'password/change/done/',
        auth_views.PasswordChangeDoneView.as_view(
            template_name='account/password_change_done.html'
        ),
        name='account_change_password_done'
    ),
    
    # Email verification
    path(
        'email/verification/sent/',
        TemplateView.as_view(template_name='account/verification_sent.html'),
        name='account_email_verification_sent'
    ),
]
