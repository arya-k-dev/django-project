#!/usr/bin/env python
"""
Test script to verify signup flow works correctly
"""
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillexchange.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User

def test_signup_flow():
    """Test that signup redirects to profile setup"""
    client = Client()
    
    # Test GET request to signup page
    response = client.get(reverse('signup'))
    assert response.status_code == 200, f"Signup page returned {response.status_code}"
    print("+ Signup page loads correctly")
    
    # Test POST request with valid data
    signup_data = {
        'username': 'testuser123',
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    
    response = client.post(reverse('signup'), signup_data)
    
    # Should redirect to profile setup after successful signup
    if response.status_code == 302:
        redirect_url = response.url
        if 'profile/setup' in redirect_url:
            print("+ Signup redirects to profile setup correctly")
            return True
        else:
            print(f"- Signup redirects to wrong URL: {redirect_url}")
            return False
    else:
        print(f"- Signup failed with status {response.status_code}")
        if response.context and 'form' in response.context:
            form_errors = response.context['form'].errors
            if form_errors:
                print(f"Form errors: {form_errors}")
        return False

def test_profile_setup_access():
    """Test that profile setup is accessible after login"""
    client = Client()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser456',
        email='test2@example.com',
        password='testpass123'
    )
    
    # Login the user
    client.login(username='testuser456', password='testpass123')
    
    # Test access to profile setup
    response = client.get(reverse('profile_setup'))
    if response.status_code == 200:
        print("+ Profile setup page is accessible after login")
        return True
    else:
        print(f"- Profile setup page returned {response.status_code}")
        return False

if __name__ == '__main__':
    print("Testing signup flow...")
    
    # Clean up any existing test users
    User.objects.filter(username__in=['testuser123', 'testuser456']).delete()
    
    success1 = test_signup_flow()
    success2 = test_profile_setup_access()
    
    if success1 and success2:
        print("\n+ All tests passed! Signup flow is working correctly.")
    else:
        print("\n- Some tests failed. Check the implementation.")
