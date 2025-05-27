from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_lecturer=True
        )
    
    def test_user_creation(self):
        """Test that a user can be created"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.is_lecturer)
        self.assertFalse(self.user.is_student)
        self.assertTrue(self.user.check_password('testpass123'))


class CoreViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            is_lecturer=True
        )
    
    def test_home_view_anonymous(self):
        """Test home view for anonymous user"""
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')
    
    def test_home_view_authenticated(self):
        """Test home view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:home'))
        # Home view should redirect authenticated users to their dashboard
        self.assertEqual(response.status_code, 302)
        # Check if it redirects to the dashboard
        self.assertIn('/dashboard/', response.url)
    
    def test_profile_view_requires_login(self):
        """Test that profile view requires login"""
        response = self.client.get(reverse('core:profile'))
        self.assertEqual(response.status_code, 302)  # Should redirect to login
        self.assertIn('/attendance/login/', response.url)
    
    def test_profile_view_authenticated(self):
        """Test profile view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/profile.html')
