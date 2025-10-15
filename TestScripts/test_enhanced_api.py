#!/usr/bin/env python3
"""
Test script for the enhanced Book Sphere API
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_api():
    print("Testing Enhanced Book Sphere API")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Health check passed: {data['status']}")
            print(f"   Books loaded: {data.get('books_loaded', 0)}")
        else:
            print(f"[ERROR] Health check failed: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Health check error: {e}")
    
    # Test 2: Register user
    print("\n2. Testing user registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", 
                               json={
                                   "username": "testuser_api",
                                   "password": "testpass123",
                                   "email": "test@api.com"
                               })
        if response.status_code == 201:
            data = response.json()
            token = data['access_token']
            print(f"[OK] User registered successfully")
            print(f"   Username: {data['user']['username']}")
            print(f"   Plan: {data['user']['plan']}")
            print(f"   Response data: {data}")
        else:
            print(f"[ERROR] Registration failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"[ERROR] Registration error: {e}")
        print(f"   Response: {response.text if 'response' in locals() else 'No response'}")
        return
    
    # Test 3: Get recommendations
    print("\n3. Testing book recommendations...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/recommendations",
                               json={
                                   "query": "science fiction",
                                   "category": "Fiction",
                                   "tone": "Happy",
                                   "top_k": 10
                               },
                               headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Recommendations received: {len(data['recommendations'])} books")
            print(f"   Query: {data['query']}")
            print(f"   Category: {data['category']}")
            print(f"   Tone: {data['tone']}")
            
            # Show first few books
            for i, book in enumerate(data['recommendations'][:3]):
                print(f"   Book {i+1}: {book['title']} by {book['authors']}")
                print(f"      ISBN: {book.get('isbn13', 'N/A')}")
                print(f"      Rating: {book.get('average_rating', 'N/A')}")
                print(f"      Cover: {book.get('large_thumbnail', 'N/A')[:50]}...")
        else:
            print(f"[ERROR] Recommendations failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Recommendations error: {e}")
    
    # Test 4: Add to library
    print("\n4. Testing add to library...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/api/user/library",
                               json={
                                   "isbn13": "9781234567890",
                                   "title": "Test Book",
                                   "authors": "Test Author",
                                   "simple_categories": "Fiction",
                                   "average_rating": 4.5,
                                   "description": "A test book",
                                   "thumbnail": "test.jpg",
                                   "large_thumbnail": "test_large.jpg"
                               },
                               headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Book added to library successfully")
            print(f"   Library count: {data['library_count']}")
            print(f"   Library limit: {data['library_limit']}")
        else:
            print(f"[ERROR] Add to library failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Add to library error: {e}")
    
    # Test 5: Get user library
    print("\n5. Testing get user library...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/api/user/library", headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Library retrieved successfully")
            print(f"   Books in library: {len(data['library'])}")
            print(f"   Plan: {data['plan']}")
            print(f"   Library limit: {data['library_limit']}")
        else:
            print(f"[ERROR] Get library failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"[ERROR] Get library error: {e}")
    
    print("\n" + "=" * 50)
    print("Enhanced API testing completed!")

if __name__ == "__main__":
    test_api()
