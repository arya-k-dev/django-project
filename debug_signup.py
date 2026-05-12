#!/usr/bin/env python
"""
Debug script to identify signup form validation issues
"""
import os
import sys
import django

# Add project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillexchange.settings')
django.setup()

from django.test import Client
from django.urls import reverse
from accounts.forms import SignUpForm

def test_form_validation():
    """Test form validation directly"""
    print("Testing form validation...")
    
    # Test valid data
    form_data = {
        'username': 'testuser123',
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'password1': 'testpass123',
        'password2': 'testpass123'
    }
    
    form = SignUpForm(data=form_data)
    
    if form.is_valid():
        print("+ Form validation passed")
        return True
    else:
        print("- Form validation failed")
        print("Errors:", form.errors)
        return False

def test_form_edge_cases():
    """Test various edge cases"""
    print("\nTesting edge cases...")
    
    test_cases = [
        {
            'name': 'Valid data',
            'data': {
                'username': 'validuser',
                'first_name': 'Valid',
                'last_name': 'User',
                'email': 'valid@example.com',
                'password1': 'validpass123',
                'password2': 'validpass123'
            }
        },
        {
            'name': 'Short password',
            'data': {
                'username': 'validuser2',
                'first_name': 'Valid',
                'last_name': 'User',
                'email': 'valid2@example.com',
                'password1': '123',
                'password2': '123'
            }
        },
        {
            'name': 'Password mismatch',
            'data': {
                'username': 'validuser3',
                'first_name': 'Valid',
                'last_name': 'User',
                'email': 'valid3@example.com',
                'password1': 'validpass123',
                'password2': 'differentpass'
            }
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['name']}")
        form = SignUpForm(data=case['data'])
        if form.is_valid():
            print(f"+ {case['name']}: Valid")
        else:
            print(f"- {case['name']}: Invalid")
            print("  Errors:", form.errors)

if __name__ == '__main__':
    test_form_validation()
    test_form_edge_cases()
