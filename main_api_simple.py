"""
Simplified Book Recommendation System API
Basic Flask server without complex ML dependencies
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
jwt = JWTManager(app)
CORS(app, origins=['http://localhost:3000', 'http://127.0.0.1:3000'])

# User management (in production, use a proper database)
users_db = {}

# Plan configurations
PLAN_LIMITS = {
    'free': {
        'daily_searches': 5,
        'monthly_searches': 50,
        'library_books': 20,
        'premium_features': False
    },
    'pro': {
        'daily_searches': 100,
        'monthly_searches': 2000,
        'library_books': 1000,
        'premium_features': True
    }
}

# API Routes

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Book Sphere API Server (Simplified)",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth/login, /api/auth/register",
            "recommendations": "/api/recommendations",
            "user": "/api/user/preferences, /api/user/history"
        },
        "frontend": "http://localhost:3000",
        "note": "This is a simplified version for testing"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "simplified"
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
        
        if username in users_db:
            return jsonify({"error": "Username already exists"}), 400
        
        # Simple password hash (in production, use proper hashing)
        import hashlib
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
            "preferences": {}
        }
        
        # Create access token
        access_token = create_access_token(identity=username)
        
        return jsonify({
            "message": "User registered successfully",
            "access_token": access_token,
            "user": {
                "username": username,
                "email": email
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
        
        # Simple password verification
        import hashlib
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

@app.route('/api/recommendations', methods=['POST'])
@jwt_required()
def get_recommendations():
    """Get book recommendations (simplified)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Mock recommendations for testing
        mock_recommendations = [
            {
                "title": "The Great Gatsby",
                "authors": "F. Scott Fitzgerald",
                "isbn13": "9780743273565",
                "average_rating": 4.5,
                "description": "A classic American novel about the Jazz Age.",
                "thumbnail": "https://example.com/gatsby.jpg"
            },
            {
                "title": "To Kill a Mockingbird",
                "authors": "Harper Lee",
                "isbn13": "9780061120084",
                "average_rating": 4.8,
                "description": "A story of racial injustice and childhood innocence.",
                "thumbnail": "https://example.com/mockingbird.jpg"
            },
            {
                "title": "1984",
                "authors": "George Orwell",
                "isbn13": "9780451524935",
                "average_rating": 4.6,
                "description": "A dystopian social science fiction novel.",
                "thumbnail": "https://example.com/1984.jpg"
            }
        ]
        
        return jsonify({
            "success": True,
            "recommendations": mock_recommendations,
            "query": query,
            "total_found": len(mock_recommendations),
            "timestamp": datetime.now().isoformat(),
            "note": "This is a simplified version with mock data"
        }), 200
        
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify({"error": "Failed to get recommendations"}), 500

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

if __name__ == '__main__':
    logger.info("Starting Book Sphere Simplified API Server")
    app.run(debug=True, host='0.0.0.0', port=5000)
