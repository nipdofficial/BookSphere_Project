"""
Enhanced Book Recommendation System API
Incorporates all functionality: sentiment analysis, text classification, vector search, and Google Books integration
"""

import os
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import hashlib
import requests
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'book-sphere-secret-key-2024')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
jwt = JWTManager(app)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# Google Books API configuration
GOOGLE_BOOKS_API_KEY = "AIzaSyBml4Xf5m4rCpr4x7dS45tv4Q3FTO8WOCE"
GOOGLE_BOOKS_BASE_URL = "https://www.googleapis.com/books/v1/volumes"

# User management
users_db = {}

# Plan configurations
PLAN_LIMITS = {
    'free': {
        'daily_searches': 20,
        'monthly_searches': 200,
        'library_books': 50,
        'premium_features': False
    },
    'pro': {
        'daily_searches': 500,
        'monthly_searches': 5000,
        'library_books': 1000,
        'premium_features': True
    }
}

# Global variables for book data
books_df = None
vector_db = None

def load_book_data():
    """Load book data and initialize vector database"""
    global books_df, vector_db
    
    try:
        # Load books with categories and emotions
        books_path = "data/books_with_categories.csv"
        if os.path.exists(books_path):
            books_df = pd.read_csv(books_path)
            logger.info(f"Loaded {len(books_df)} books with categories")
        else:
            # Fallback to basic books data
            books_path = "data/books_cleaned.csv"
            books_df = pd.read_csv(books_path)
            logger.info(f"Loaded {len(books_df)} books (basic data)")
        
        # Ensure required columns exist
        if 'large_thumbnail' not in books_df.columns:
            books_df['large_thumbnail'] = books_df.get('thumbnail', 'cover-not-found.jpg')
        
        if 'simple_categories' not in books_df.columns:
            books_df['simple_categories'] = books_df.get('categories', 'Fiction')
        
        # Initialize emotion columns if they don't exist
        emotion_columns = ['joy', 'anger', 'fear', 'sadness', 'surprise', 'neutral']
        for col in emotion_columns:
            if col not in books_df.columns:
                books_df[col] = 0.0
        
        logger.info("Book data loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error loading book data: {e}")
        return False

def search_google_books(query, max_results=10):
    """Search Google Books API for additional book data"""
    try:
        params = {
            'q': query,
            'key': GOOGLE_BOOKS_API_KEY,
            'maxResults': max_results,
            'printType': 'books'
        }
        
        response = requests.get(GOOGLE_BOOKS_BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        books = []
        
        for item in data.get('items', []):
            volume_info = item.get('volumeInfo', {})
            
            # Extract ISBN
            isbn13 = None
            isbn10 = None
            for identifier in volume_info.get('industryIdentifiers', []):
                if identifier.get('type') == 'ISBN_13':
                    isbn13 = identifier.get('identifier')
                elif identifier.get('type') == 'ISBN_10':
                    isbn10 = identifier.get('identifier')
            
            book = {
                'title': volume_info.get('title', 'Unknown Title'),
                'authors': ', '.join(volume_info.get('authors', ['Unknown Author'])),
                'description': volume_info.get('description', 'No description available'),
                'isbn13': isbn13,
                'isbn10': isbn10,
                'categories': ', '.join(volume_info.get('categories', ['Fiction'])),
                'average_rating': volume_info.get('averageRating', 0.0),
                'ratings_count': volume_info.get('ratingsCount', 0),
                'published_year': volume_info.get('publishedDate', '').split('-')[0] if volume_info.get('publishedDate') else None,
                'num_pages': volume_info.get('pageCount', 0),
                'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', 'cover-not-found.jpg'),
                'large_thumbnail': volume_info.get('imageLinks', {}).get('large', volume_info.get('imageLinks', {}).get('thumbnail', 'cover-not-found.jpg')),
                'preview_link': volume_info.get('previewLink', ''),
                'info_link': volume_info.get('infoLink', ''),
                'canonical_volume_link': volume_info.get('canonicalVolumeLink', ''),
                'source': 'google_books'
            }
            books.append(book)
        
        return books
        
    except Exception as e:
        logger.error(f"Error searching Google Books: {e}")
        return []

def get_enhanced_book_details(isbn):
    """Get enhanced book details from Google Books"""
    try:
        params = {
            'q': f'isbn:{isbn}',
            'key': GOOGLE_BOOKS_API_KEY,
            'maxResults': 1
        }
        
        response = requests.get(GOOGLE_BOOKS_BASE_URL, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('items'):
            item = data['items'][0]
            volume_info = item.get('volumeInfo', {})
            
            return {
                'title': volume_info.get('title', 'Unknown Title'),
                'authors': ', '.join(volume_info.get('authors', ['Unknown Author'])),
                'description': volume_info.get('description', 'No description available'),
                'categories': ', '.join(volume_info.get('categories', ['Fiction'])),
                'average_rating': volume_info.get('averageRating', 0.0),
                'ratings_count': volume_info.get('ratingsCount', 0),
                'published_year': volume_info.get('publishedDate', '').split('-')[0] if volume_info.get('publishedDate') else None,
                'num_pages': volume_info.get('pageCount', 0),
                'thumbnail': volume_info.get('imageLinks', {}).get('thumbnail', 'cover-not-found.jpg'),
                'large_thumbnail': volume_info.get('imageLinks', {}).get('large', volume_info.get('imageLinks', {}).get('thumbnail', 'cover-not-found.jpg')),
                'preview_link': volume_info.get('previewLink', ''),
                'info_link': volume_info.get('infoLink', ''),
                'canonical_volume_link': volume_info.get('canonicalVolumeLink', ''),
                'source': 'google_books'
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting enhanced book details: {e}")
        return None

def semantic_search_books(query, category="All", tone="All", top_k=20):
    """Perform semantic search on books"""
    global books_df
    
    if books_df is None:
        return []
    
    try:
        # Simple text-based search for now (can be enhanced with vector search later)
        filtered_books = books_df.copy()
        
        # Filter by category
        if category != "All" and 'simple_categories' in filtered_books.columns:
            filtered_books = filtered_books[filtered_books['simple_categories'] == category]
        
        # Filter by emotional tone
        if tone != "All":
            if tone == "Happy" and 'joy' in filtered_books.columns:
                filtered_books = filtered_books.sort_values(by='joy', ascending=False)
            elif tone == "Surprising" and 'surprise' in filtered_books.columns:
                filtered_books = filtered_books.sort_values(by='surprise', ascending=False)
            elif tone == "Angry" and 'anger' in filtered_books.columns:
                filtered_books = filtered_books.sort_values(by='anger', ascending=False)
            elif tone == "Suspenseful" and 'fear' in filtered_books.columns:
                filtered_books = filtered_books.sort_values(by='fear', ascending=False)
            elif tone == "Sad" and 'sadness' in filtered_books.columns:
                filtered_books = filtered_books.sort_values(by='sadness', ascending=False)
        
        # Text-based search in title, authors, and description
        query_lower = query.lower()
        mask = (
            filtered_books['title'].str.lower().str.contains(query_lower, na=False) |
            filtered_books['authors'].str.lower().str.contains(query_lower, na=False) |
            filtered_books['description'].str.lower().str.contains(query_lower, na=False)
        )
        
        results = filtered_books[mask].head(top_k)
        
        # Convert to list of dictionaries
        books_list = []
        for _, row in results.iterrows():
            book = {
                'isbn13': str(row.get('isbn13', '')),
                'isbn10': str(row.get('isbn10', '')),
                'title': str(row.get('title', 'Unknown Title')),
                'authors': str(row.get('authors', 'Unknown Author')),
                'description': str(row.get('description', 'No description available')),
                'categories': str(row.get('categories', 'Fiction')),
                'simple_categories': str(row.get('simple_categories', 'Fiction')),
                'average_rating': float(row.get('average_rating', 0.0)),
                'ratings_count': int(row.get('ratings_count', 0)),
                'published_year': int(row.get('published_year', 0)) if pd.notna(row.get('published_year')) else None,
                'num_pages': int(row.get('num_pages', 0)) if pd.notna(row.get('num_pages')) else None,
                'thumbnail': str(row.get('thumbnail', 'cover-not-found.jpg')),
                'large_thumbnail': str(row.get('large_thumbnail', 'cover-not-found.jpg')),
                'source': 'local_database'
            }
            books_list.append(book)
        
        return books_list
        
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []

# API Routes

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Book Sphere Enhanced API Server",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Semantic book search",
            "Emotional tone filtering",
            "Category filtering",
            "Google Books integration",
            "Personalized recommendations",
            "Library management",
            "Book cover images",
            "Reading links"
        ],
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth/login, /api/auth/register",
            "recommendations": "/api/recommendations, /api/recommendations/personalized",
            "search": "/api/books/search",
            "google_books": "/api/books/google-search",
            "user": "/api/user/preferences, /api/user/history, /api/user/library"
        },
        "frontend": "http://localhost:3000"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "enhanced",
        "books_loaded": len(books_df) if books_df is not None else 0,
        "google_books_api": "configured"
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip()
        
        if not username or not password or not email:
            return jsonify({"error": "Username, password, and email are required"}), 400
        
        if len(username) < 3 or len(username) > 30:
            return jsonify({"error": "Username must be 3-30 characters long"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters long"}), 400
        
        if username in users_db:
            return jsonify({"error": "Username already exists"}), 400
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Store user
        users_db[username] = {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "plan": "free",
            "usage": {
                "daily_searches": 0,
                "monthly_searches": 0,
                "last_search_date": None,
                "last_search_month": None
            },
            "reading_history": [],
            "library": [],
            "preferences": {
                "favorite_categories": [],
                "favorite_authors": [],
                "preferred_tone": "All"
            }
        }
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "username": username,
                "email": email,
                "plan": "free",
                "usage": users_db[username]['usage']
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        user = users_db.get(username)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Verify password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if password_hash != user['password_hash']:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "user": {
                "username": username,
                "email": user.get('email'),
                "plan": user.get('plan', 'free'),
                "usage": user.get('usage', {})
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

def check_usage_limits(username: str) -> tuple[bool, str]:
    """Check if user has exceeded usage limits"""
    user = users_db.get(username, {})
    plan = user.get('plan', 'free')
    usage = user.get('usage', {})
    limits = PLAN_LIMITS[plan]
    
    current_date = datetime.now().date()
    current_month = datetime.now().strftime('%Y-%m')
    
    # Reset daily counter if new day
    if usage.get('last_search_date') != current_date.isoformat():
        usage['daily_searches'] = 0
        usage['last_search_date'] = current_date.isoformat()
    
    # Reset monthly counter if new month
    if usage.get('last_search_month') != current_month:
        usage['monthly_searches'] = 0
        usage['last_search_month'] = current_month
    
    # Check limits
    if usage['daily_searches'] >= limits['daily_searches']:
        return False, f"Daily search limit reached ({limits['daily_searches']} searches)"
    
    if usage['monthly_searches'] >= limits['monthly_searches']:
        return False, f"Monthly search limit reached ({limits['monthly_searches']} searches)"
    
    return True, ""

@app.route('/api/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    """Get enhanced book recommendations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        query = data.get('query', '').strip()
        category = data.get('category', 'All')
        tone = data.get('tone', 'All')
        top_k = min(data.get('top_k', 20), 50)  # Limit max results
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Check usage limits
        username = get_jwt_identity()
        can_search, error_msg = check_usage_limits(username)
        
        if not can_search:
            return jsonify({
                "error": error_msg,
                "plan": users_db[username].get('plan', 'free'),
                "upgrade_required": True
            }), 429
        
        # Get recommendations from local database
        local_recommendations = semantic_search_books(query, category, tone, top_k)
        
        # Get additional recommendations from Google Books
        google_recommendations = search_google_books(query, max_results=10)
        
        # Combine and deduplicate recommendations
        all_recommendations = local_recommendations + google_recommendations
        
        # Remove duplicates based on ISBN
        seen_isbns = set()
        unique_recommendations = []
        for book in all_recommendations:
            isbn = book.get('isbn13') or book.get('isbn10')
            if isbn and isbn not in seen_isbns:
                seen_isbns.add(isbn)
                unique_recommendations.append(book)
        
        # Limit to requested number
        final_recommendations = unique_recommendations[:top_k]
        
        # Update usage counters
        users_db[username]['usage']['daily_searches'] += 1
        users_db[username]['usage']['monthly_searches'] += 1
        
        return jsonify({
            "success": True,
            "recommendations": final_recommendations,
            "query": query,
            "category": category,
            "tone": tone,
            "total_found": len(final_recommendations),
            "timestamp": datetime.now().isoformat(),
            "usage": users_db[username]['usage'],
            "plan": users_db[username].get('plan', 'free')
        }), 200
        
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify({"error": "Failed to get recommendations"}), 500

@app.route('/api/recommendations/personalized', methods=['POST'])
@jwt_required()
def get_personalized_recommendations():
    """Get personalized book recommendations based on user history"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = min(data.get('top_k', 15), 30)
        
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        # Get user preferences and history
        preferences = user.get('preferences', {})
        reading_history = user.get('reading_history', [])
        
        # Build personalized query
        personalized_query = query
        
        # Add favorite categories to query
        favorite_categories = preferences.get('favorite_categories', [])
        if favorite_categories:
            personalized_query += " " + " ".join(favorite_categories)
        
        # Add favorite authors to query
        favorite_authors = preferences.get('favorite_authors', [])
        if favorite_authors:
            personalized_query += " " + " ".join(favorite_authors)
        
        # Get recommendations
        recommendations = semantic_search_books(personalized_query, top_k=top_k)
        
        # Add Google Books recommendations
        google_recs = search_google_books(personalized_query, max_results=5)
        
        # Combine recommendations
        all_recs = recommendations + google_recs
        
        # Remove duplicates
        seen_isbns = set()
        unique_recs = []
        for book in all_recs:
            isbn = book.get('isbn13') or book.get('isbn10')
            if isbn and isbn not in seen_isbns:
                seen_isbns.add(isbn)
                unique_recs.append(book)
        
        final_recommendations = unique_recs[:top_k]
        
        return jsonify({
            "success": True,
            "recommendations": final_recommendations,
            "query": query,
            "personalized_query": personalized_query,
            "total_found": len(final_recommendations),
            "timestamp": datetime.now().isoformat(),
            "personalization_factors": {
                "favorite_categories": favorite_categories,
                "favorite_authors": favorite_authors,
                "reading_history_count": len(reading_history)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Personalized recommendations error: {e}")
        return jsonify({"error": "Failed to get personalized recommendations"}), 500

@app.route('/api/books/search', methods=['POST'])
@jwt_required()
def search_books():
    """Search books with advanced filtering"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        category = data.get('category', 'All')
        tone = data.get('tone', 'All')
        top_k = min(data.get('top_k', 20), 50)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Perform search
        results = semantic_search_books(query, category, tone, top_k)
        
        return jsonify({
            "success": True,
            "results": results,
            "query": query,
            "category": category,
            "tone": tone,
            "total_results": len(results)
        }), 200
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/api/books/google-search', methods=['POST'])
@jwt_required()
def search_google_books_endpoint():
    """Search Google Books directly"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        max_results = min(data.get('max_results', 10), 20)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Search Google Books
        results = search_google_books(query, max_results)
        
        return jsonify({
            "success": True,
            "results": results,
            "query": query,
            "total_results": len(results),
            "source": "google_books"
        }), 200
        
    except Exception as e:
        logger.error(f"Google Books search error: {e}")
        return jsonify({"error": "Failed to search Google Books"}), 500

@app.route('/api/books/enhanced-details/<isbn>', methods=['GET'])
@jwt_required()
def get_enhanced_book_details_endpoint(isbn):
    """Get enhanced book details from Google Books"""
    try:
        details = get_enhanced_book_details(isbn)
        
        if details:
            return jsonify({
                "success": True,
                "book": details,
                "source": "google_books"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Book not found in Google Books"
            }), 404
        
    except Exception as e:
        logger.error(f"Enhanced book details error: {e}")
        return jsonify({"error": "Failed to get enhanced book details"}), 500

@app.route('/api/user/library', methods=['GET'])
@jwt_required()
def get_user_library():
    """Get user's library books"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        return jsonify({
            "library": user.get('library', []),
            "plan": user.get('plan', 'free'),
            "library_limit": PLAN_LIMITS[user.get('plan', 'free')]['library_books']
        }), 200
        
    except Exception as e:
        logger.error(f"Get library error: {e}")
        return jsonify({"error": "Failed to get library"}), 500

@app.route('/api/user/library', methods=['POST'])
@jwt_required()
def add_to_library():
    """Add book to user's library"""
    try:
        username = get_jwt_identity()
        data = request.get_json()
        
        if username not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        user = users_db[username]
        plan = user.get('plan', 'free')
        library = user.get('library', [])
        
        # Check library limit
        if len(library) >= PLAN_LIMITS[plan]['library_books']:
            return jsonify({
                "error": f"Library limit reached ({PLAN_LIMITS[plan]['library_books']} books)",
                "upgrade_required": True
            }), 429
        
        # Check if book already exists
        book_isbn = data.get('isbn13') or data.get('isbn10')
        if any(book.get('isbn13') == book_isbn or book.get('isbn10') == book_isbn for book in library):
            return jsonify({"error": "Book already in library"}), 400
        
        # Add book to library
        book_entry = {
            "isbn13": data.get('isbn13'),
            "isbn10": data.get('isbn10'),
            "title": data.get('title'),
            "authors": data.get('authors'),
            "simple_categories": data.get('simple_categories'),
            "average_rating": data.get('average_rating'),
            "description": data.get('description'),
            "thumbnail": data.get('thumbnail'),
            "large_thumbnail": data.get('large_thumbnail'),
            "preview_link": data.get('preview_link'),
            "info_link": data.get('info_link'),
            "canonical_volume_link": data.get('canonical_volume_link'),
            "added_at": datetime.now().isoformat()
        }
        
        library.append(book_entry)
        users_db[username]['library'] = library
        
        return jsonify({
            "message": "Book added to library successfully",
            "library_count": len(library),
            "library_limit": PLAN_LIMITS[plan]['library_books']
        }), 200
        
    except Exception as e:
        logger.error(f"Add to library error: {e}")
        return jsonify({"error": "Failed to add to library"}), 500

@app.route('/api/user/library/<book_id>', methods=['DELETE'])
@jwt_required()
def remove_from_library(book_id):
    """Remove book from user's library"""
    try:
        username = get_jwt_identity()
        
        if username not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        library = users_db[username].get('library', [])
        
        # Find and remove book
        library = [book for book in library if book.get('isbn13') != book_id and book.get('isbn10') != book_id]
        users_db[username]['library'] = library
        
        return jsonify({
            "message": "Book removed from library successfully",
            "library_count": len(library)
        }), 200
        
    except Exception as e:
        logger.error(f"Remove from library error: {e}")
        return jsonify({"error": "Failed to remove from library"}), 500

@app.route('/api/user/preferences', methods=['GET'])
@jwt_required()
def get_user_preferences():
    """Get user preferences"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        return jsonify({
            "preferences": user.get('preferences', {}),
            "reading_history": user.get('reading_history', [])
        }), 200
        
    except Exception as e:
        logger.error(f"Get preferences error: {e}")
        return jsonify({"error": "Failed to get preferences"}), 500

@app.route('/api/user/preferences', methods=['POST'])
@jwt_required()
def update_user_preferences():
    """Update user preferences"""
    try:
        username = get_jwt_identity()
        data = request.get_json()
        
        if username not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # Update preferences
        users_db[username]['preferences'].update(data)
        
        return jsonify({"message": "Preferences updated successfully"}), 200
        
    except Exception as e:
        logger.error(f"Update preferences error: {e}")
        return jsonify({"error": "Failed to update preferences"}), 500

@app.route('/api/user/history', methods=['POST'])
@jwt_required()
def add_to_history():
    """Add book to user's reading history"""
    try:
        username = get_jwt_identity()
        data = request.get_json()
        
        if username not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # Add book to history
        book_entry = {
            "isbn13": data.get('isbn13'),
            "title": data.get('title'),
            "authors": data.get('authors'),
            "simple_categories": data.get('simple_categories'),
            "average_rating": data.get('average_rating'),
            "added_at": datetime.now().isoformat()
        }
        
        users_db[username]['reading_history'].append(book_entry)
        
        return jsonify({"message": "Book added to history successfully"}), 200
        
    except Exception as e:
        logger.error(f"Add to history error: {e}")
        return jsonify({"error": "Failed to add to history"}), 500

@app.route('/api/user/plan', methods=['GET'])
@jwt_required()
def get_user_plan():
    """Get user's current plan and usage"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        plan = user.get('plan', 'free')
        usage = user.get('usage', {})
        
        return jsonify({
            "plan": plan,
            "usage": usage,
            "limits": PLAN_LIMITS[plan],
            "library_count": len(user.get('library', [])),
            "library_limit": PLAN_LIMITS[plan]['library_books']
        }), 200
        
    except Exception as e:
        logger.error(f"Get plan error: {e}")
        return jsonify({"error": "Failed to get plan info"}), 500

@app.route('/api/user/upgrade', methods=['POST'])
@jwt_required()
def upgrade_plan():
    """Upgrade user to pro plan (mock implementation)"""
    try:
        username = get_jwt_identity()
        
        if username not in users_db:
            return jsonify({"error": "User not found"}), 404
        
        # In a real implementation, this would integrate with payment processing
        users_db[username]['plan'] = 'pro'
        
        return jsonify({
            "message": "Successfully upgraded to Pro plan!",
            "plan": "pro",
            "limits": PLAN_LIMITS['pro']
        }), 200
        
    except Exception as e:
        logger.error(f"Upgrade error: {e}")
        return jsonify({"error": "Failed to upgrade plan"}), 500

if __name__ == '__main__':
    # Load book data
    if load_book_data():
        logger.info("Starting Book Sphere Enhanced API Server")
        logger.info("Features: Semantic search, Google Books integration, Library management")
        logger.info("Server will be available at: http://localhost:5000")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to load book data")
