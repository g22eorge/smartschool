from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, UpdateView

from .forms import CustomUserChangeForm
from .models import User


class ProfileView(LoginRequiredMixin, DetailView):
    """Display the user's profile."""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user_profile'
    
    def get_object(self, queryset=None):
        """
        Return the user's own profile.
        """
        return self.request.user


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update the user's profile."""
    model = User
    form_class = CustomUserChangeForm
    template_name = 'users/profile_edit.html'
    success_url = reverse_lazy('users:profile')
    
    def get_object(self, queryset=None):
        """
        Return the user's own profile.
        """
        return self.request.user
    
    def form_valid(self, form):
        """
        If the form is valid, save the associated model and show a success message.
        """
        messages.success(self.request, _('Your profile has been updated successfully.'))
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        """
        Add request to form kwargs for file uploads.
        """
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
