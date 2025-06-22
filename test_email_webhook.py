#!/usr/bin/env python3
"""
Test script for the Flask email webhook - Friends Trip Planning
This script simulates webhook requests from your friends about the Greece trip
"""

import requests
import json
from urllib.parse import urlencode

def test_webhook_endpoint(webhook_url, friend_email, friend_name, message):
    """Test the webhook endpoint with a simulated email from a friend"""
    
    # Simulate email data that SendGrid would send
    email_data = {
        'from': friend_email,
        'to': 'replies@mail.yourdomain.com',
        'subject': f'Re: Greece Trip Planning',
        'text': message,
        'html': f'<p>{message}</p>',
        'headers': f'From: {friend_email}\r\nTo: replies@mail.yourdomain.com\r\nSubject: Re: Greece Trip Planning',
        'dkim': 'pass',
        'spam_report': '0',
        'envelope': f'{{"to":"replies@mail.yourdomain.com","from":"{friend_email}"}}',
        'attachments': '0',
        'charsets': '{"to":"UTF-8","html":"UTF-8","subject":"UTF-8","from":"UTF-8","text":"UTF-8"}',
        'SPF': 'pass'
    }
    
    try:
        # Send POST request to webhook
        response = requests.post(
            webhook_url,
            data=urlencode(email_data),
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print(f"✅ Webhook test successful for {friend_name}!")
            return True
        else:
            print(f"❌ Webhook test failed for {friend_name}!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing webhook for {friend_name}: {str(e)}")
        return False

def test_health_endpoint(webhook_url):
    """Test the health check endpoint"""
    
    try:
        response = requests.get(webhook_url)
        
        print(f"Health Check Status Code: {response.status_code}")
        print(f"Health Check Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Health check successful!")
            return True
        else:
            print("❌ Health check failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing health endpoint: {str(e)}")
        return False

def test_local_flask_app():
    """Test the local Flask app if running"""
    local_url = "http://localhost:5000/webhook/sendgrid"
    
    print("Testing local Flask app for Friends Trip Planning...")
    print("=" * 60)
    
    # Test health endpoint first
    print("\n1. Testing health endpoint...")
    health_ok = test_health_endpoint(local_url)
    
    if health_ok:
        print("\n2. Testing webhook with simulated emails from friends...")
        
        # Test emails from each friend
        friends_tests = [
            {
                "email": "drey@proximus.be",
                "name": "Dominique",
                "message": "Hi Nini! I'm so excited about the Greece trip! I found some amazing hiking trails in Crete, especially around the Samaria Gorge. The views look absolutely breathtaking! When do you think we should go? I'm thinking spring would be perfect for hiking."
            },
            {
                "email": "vladimirmylle@hotmail.be", 
                "name": "Vladimir",
                "message": "Nini! I've been researching ancient ruins in Greece and I'm blown away! The Acropolis in Athens is a must-see, and I found some incredible historical sites in Delphi. Maybe I can lead a historical tour one day? This is going to be amazing!"
            },
            {
                "email": "laura.mylle@hotmail.com",
                "name": "Laura", 
                "message": "Hey Nini! The local art scene in Athens looks incredible! I found some amazing galleries and museums. I can't wait to sketch the ancient architecture and capture the local culture. This trip is going to be so inspiring!"
            }
        ]
        
        all_tests_passed = True
        for friend in friends_tests:
            print(f"\n   Testing response from {friend['name']}...")
            test_result = test_webhook_endpoint(
                local_url, 
                friend['email'], 
                friend['name'], 
                friend['message']
            )
            if not test_result:
                all_tests_passed = False
        
        if all_tests_passed:
            print("\n🎉 All friend tests passed! Your trip planning webhook is working correctly!")
        else:
            print("\n⚠️  Some friend tests failed. Check your Flask app logs.")
    else:
        print("\n❌ Local health check failed. Make sure your Flask app is running:")
        print("   python email_responder.py")

if __name__ == "__main__":
    print("Friends Trip Planning Webhook Testing Tool")
    print("=" * 60)
    
    # Test local Flask app if available
    test_local_flask_app()
    
    print("\n" + "=" * 60)
    print("To test your deployed webhook:")
    print("1. Replace 'your-app-url' with your actual deployment URL")
    print("2. Uncomment the lines below and run the script")
    print("3. Or test manually with curl commands from the setup guide")
    
    # Uncomment and modify the URL below to test your deployed webhook
    # webhook_url = "https://your-app-url.vercel.app/webhook/sendgrid"
    # test_health_endpoint(webhook_url)
    # 
    # # Test with Dominique's email
    # test_webhook_endpoint(
    #     webhook_url,
    #     "drey@proximus.be",
    #     "Dominique", 
    #     "Hi Nini! I found some amazing hiking trails in Crete!"
    # ) 