#!/usr/bin/env python3
"""
Test script to verify onboarding flow works correctly
"""
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillexchange.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth.models import User
from accounts.models import UserProfile

def test_onboarding_step1():
    """Test that onboarding step 1 form validates and redirects correctly"""
    print("Testing onboarding step 1...")
    
    # Clean up any existing test data
    User.objects.filter(username__in=['testuser', 'testuser2']).delete()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    # Create client and login
    client = Client()
    client.login(username='testuser', password='testpass123')
    
    # Test GET request
    response = client.get('/accounts/onboarding/step1/')
    assert response.status_code == 200, f"GET request failed: {response.status_code}"
    
    # Test POST request with minimal data
    response = client.post('/accounts/onboarding/step1/', {
        'bio': 'Test bio for user',
        'location': 'Test City',
        'availability': 'flexible',
        'timeline_milestones_json': '',
    })
    
    if response.status_code == 302:
        print("✓ Step 1 form submission successful - redirecting to step 2")
        assert '/accounts/onboarding/step2/' in response.url, f"Wrong redirect URL: {response.url}"
    else:
        print(f"✗ Step 1 form submission failed with status {response.status_code}")
        if 'form' in response.context:
            print(f"Form errors: {response.context['form'].errors}")
        return False
    
    # Clean up
    User.objects.filter(username='testuser').delete()
    return True

def test_onboarding_step2():
    """Test that onboarding step 2 works correctly"""
    print("Testing onboarding step 2...")
    
    # Clean up any existing test data
    User.objects.filter(username='testuser2').delete()
    
    # Create a test user
    user = User.objects.create_user(
        username='testuser2',
        email='test2@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    # Create client and login
    client = Client()
    client.login(username='testuser2', password='testpass123')
    
    # Test GET request
    response = client.get('/accounts/onboarding/step2/')
    assert response.status_code == 200, f"GET request failed: {response.status_code}"
    
    # Clean up
    User.objects.filter(username='testuser2').delete()
    return True

if __name__ == '__main__':
    print("Running onboarding flow tests...")
    print("=" * 50)
    
    try:
        success1 = test_onboarding_step1()
        success2 = test_onboarding_step2()
        
        if success1 and success2:
            print("\n✓ All tests passed! Onboarding flow should work correctly.")
        else:
            print("\n✗ Some tests failed. Check the output above for details.")
            
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
