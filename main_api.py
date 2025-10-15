"""
Multi-Agent Book Recommendation System
Main orchestrator and API endpoints
"""

import os
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Import our agents
from agents.base_agent import AgentCommunicationHub
from agents.classification_agent import ClassificationAgent
from agents.popularity_agent import PopularityAnalyzerAgent
from agents.suggestion_agent import SuggestionAgent

# Import vector search components
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Import Google Books integration
from pyScripts.google_books_integration import create_enhanced_system

# Import security utilities
from pyScripts.security_utils import (
    InputSanitizer, EncryptionUtils, SecurityHeaders, 
    AuditLogger, validate_request_data, check_rate_limit
)

# Import ethical AI utilities
from pyScripts.ethical_ai_utils import ethical_ai_monitor, transparency_reporter

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

# Add security headers to all responses
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    for header, value in SecurityHeaders.get_security_headers().items():
        response.headers[header] = value
    return response

# Global variables
communication_hub = AgentCommunicationHub()
books_df = None
vector_db = None
enhanced_system = None

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

class BookRecommendationSystem:
    """Main system orchestrator"""
    
    def __init__(self):
        self.hub = AgentCommunicationHub()
        self.books_df = None
        self.vector_db = None
        self.agents = {}
        
    def initialize_system(self, books_path: str, vector_db_path: str):
        """Initialize the multi-agent system"""
        try:
            # Load books data
            self.books_df = pd.read_csv(books_path)
            logger.info(f"Loaded {len(self.books_df)} books")
            
            # Initialize embeddings and vector database
            embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            self.vector_db = Chroma(persist_directory=vector_db_path, embedding_function=embeddings)
            logger.info("Vector database loaded")
            
            # Initialize agents
            self.classification_agent = ClassificationAgent()
            self.popularity_agent = PopularityAnalyzerAgent()
            self.suggestion_agent = SuggestionAgent()
            
            # Set agent references
            self.suggestion_agent.set_agent_references(
                self.classification_agent, 
                self.popularity_agent
            )
            self.suggestion_agent.set_data_sources(self.vector_db, self.books_df)
            
            # Register agents with communication hub
            self.hub.register_agent(self.classification_agent)
            self.hub.register_agent(self.popularity_agent)
            self.hub.register_agent(self.suggestion_agent)
            
            # Store agent references
            self.agents = {
                "classification": self.classification_agent,
                "popularity": self.popularity_agent,
                "suggestion": self.suggestion_agent
            }
            
            logger.info("Multi-agent system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing system: {e}")
            return False
    
    def get_recommendations(self, query: str, filters: Dict[str, Any] = None, 
                          user_preferences: Dict[str, Any] = None, 
                          top_k: int = 10) -> Dict[str, Any]:
        """Get book recommendations using multi-agent system"""
        try:
            # Create message for suggestion agent
            message_content = {
                "query": query,
                "filters": filters or {},
                "user_preferences": user_preferences or {},
                "top_k": top_k
            }
            
            # Send message through communication hub
            message = self.suggestion_agent.send_message(
                self.suggestion_agent.agent_id,
                "get_recommendations",
                message_content
            )
            
            # Process message
            response = self.suggestion_agent.process_message(message)
            
            if response and response.message_type == "recommendation_result":
                return {
                    "success": True,
                    "recommendations": response.content["recommendations"],
                    "query": response.content["query"],
                    "total_found": response.content["total_found"],
                    "timestamp": response.content["processing_timestamp"]
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to get recommendations",
                    "recommendations": []
                }
                
        except Exception as e:
            logger.error(f"Error getting recommendations: {e}")
            return {
                "success": False,
                "error": str(e),
                "recommendations": []
            }
    
    def analyze_user_preferences(self, query: str, user_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Analyze user preferences"""
        try:
            message_content = {
                "query": query,
                "user_history": user_history or []
            }
            
            message = self.suggestion_agent.send_message(
                self.suggestion_agent.agent_id,
                "analyze_user_preferences",
                message_content
            )
            
            response = self.suggestion_agent.process_message(message)
            
            if response and response.message_type == "preference_analysis_result":
                return {
                    "success": True,
                    "preferences": response.content["combined_preferences"],
                    "analysis": response.content
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to analyze preferences"
                }
                
        except Exception as e:
            logger.error(f"Error analyzing preferences: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "system_initialized": self.books_df is not None and self.vector_db is not None,
            "total_books": len(self.books_df) if self.books_df is not None else 0,
            "agents_status": self.hub.get_system_status(),
            "timestamp": datetime.now().isoformat()
        }

# Initialize system
recommendation_system = BookRecommendationSystem()

# API Routes

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        "message": "Book Sphere Multi-Agent API Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "auth": "/api/auth/login, /api/auth/register",
            "recommendations": "/api/recommendations, /api/recommendations/personalized",
            "user": "/api/user/preferences, /api/user/history",
            "search": "/api/books/search",
            "commercialization": "/api/commercialization/book-links"
        },
        "frontend": "http://localhost:3000",
        "documentation": "See README.md for full API documentation"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    status = recommendation_system.get_system_status()
    return jsonify({
        "status": "healthy" if status["system_initialized"] else "initializing",
        "details": status
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint"""
    try:
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        if not check_rate_limit(f"register_{client_ip}", max_requests=5, window_seconds=300):
            AuditLogger.log_rate_limit_exceeded(f"register_{client_ip}", client_ip)
            return jsonify({"error": "Too many registration attempts. Please try again later."}), 429
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Validate and sanitize input
        validation = validate_request_data(data, ['username', 'password', 'email'])
        if not validation['valid']:
            return jsonify({"error": "; ".join(validation['errors'])}), 400
        
        sanitized_data = validation['sanitized_data']
        username = sanitized_data['username']
        password = sanitized_data['password']
        email = sanitized_data['email']
        
        # Validate input formats
        if not InputSanitizer.validate_username(username):
            return jsonify({"error": "Invalid username format. Use 3-30 alphanumeric characters and underscores only."}), 400
        
        if not InputSanitizer.validate_email(email):
            return jsonify({"error": "Invalid email format"}), 400
        
        password_validation = InputSanitizer.validate_password(password)
        if not password_validation['valid']:
            return jsonify({"error": "; ".join(password_validation['errors'])}), 400
        
        if username in users_db:
            return jsonify({"error": "Username already exists"}), 400
        
        # Hash password using secure method
        password_hash = EncryptionUtils.hash_password(password)
        
        # Store user
        users_db[username] = {
            "username": username,
            "password_hash": password_hash,
            "email": email,
            "created_at": datetime.now().isoformat(),
            "plan": "free",  # Default to free plan
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
        # Rate limiting
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR'))
        if not check_rate_limit(f"login_{client_ip}", max_requests=10, window_seconds=300):
            AuditLogger.log_rate_limit_exceeded(f"login_{client_ip}", client_ip)
            return jsonify({"error": "Too many login attempts. Please try again later."}), 429
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Validate and sanitize input
        validation = validate_request_data(data, ['username', 'password'])
        if not validation['valid']:
            return jsonify({"error": "; ".join(validation['errors'])}), 400
        
        sanitized_data = validation['sanitized_data']
        username = sanitized_data['username']
        password = sanitized_data['password']
        
        user = users_db.get(username)
        if not user or not EncryptionUtils.verify_password(password, user['password_hash']):
            # Log failed login attempt
            user_agent = request.headers.get('User-Agent', 'Unknown')
            AuditLogger.log_failed_login(username, client_ip, user_agent)
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
    """Get book recommendations"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        # Validate and sanitize input
        validation = validate_request_data(data, ['query'])
        if not validation['valid']:
            return jsonify({"error": "; ".join(validation['errors'])}), 400
        
        sanitized_data = validation['sanitized_data']
        query = InputSanitizer.sanitize_search_query(sanitized_data['query'])
        filters = data.get('filters', {})
        top_k = min(data.get('top_k', 10), 50)  # Limit max results
        
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
        
        # Get user preferences
        user = users_db.get(username, {})
        user_preferences = user.get('preferences', {})
        user_history = user.get('reading_history', [])
        
        # Get recommendations
        import time
        start_time = time.time()
        
        result = recommendation_system.get_recommendations(
            query=query,
            filters=filters,
            user_preferences=user_preferences,
            top_k=top_k
        )
        
        processing_time = time.time() - start_time
        
        # Enhance with Google Books if available
        if result['success'] and enhanced_system:
            try:
                enhanced_recommendations = enhanced_system.enhance_recommendations(
                    result['recommendations'], query
                )
                result['recommendations'] = enhanced_recommendations
                result['enhanced_with_google_books'] = True
            except Exception as e:
                logger.error(f"Error enhancing with Google Books: {e}")
                result['enhanced_with_google_books'] = False
        
        # Log recommendation decision for ethical AI monitoring
        if result['success']:
            ethical_ai_monitor.log_recommendation_decision(
                query=query,
                recommendations=result['recommendations'],
                user_id=username,
                algorithm_used='multi_agent_system',
                processing_time=processing_time,
                metadata={
                    'filters_applied': filters,
                    'top_k': top_k,
                    'enhanced_with_google_books': result.get('enhanced_with_google_books', False)
                }
            )
            
            # Add explanation for transparency
            result['explanation'] = ethical_ai_monitor.get_recommendation_explanation(
                query=query,
                recommendations=result['recommendations'],
                algorithm_used='multi_agent_system'
            )
        
        # Update usage counters
        if result['success']:
            users_db[username]['usage']['daily_searches'] += 1
            users_db[username]['usage']['monthly_searches'] += 1
        
        # Add usage info to response
        result['usage'] = users_db[username]['usage']
        result['plan'] = users_db[username].get('plan', 'free')
        
        return jsonify(result), 200 if result['success'] else 500
        
    except Exception as e:
        logger.error(f"Recommendations error: {e}")
        return jsonify({"error": "Failed to get recommendations"}), 500

@app.route('/api/recommendations/personalized', methods=['POST'])
@jwt_required()
def get_personalized_recommendations():
    """Get personalized book recommendations"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Get user data
        username = get_jwt_identity()
        user = users_db.get(username, {})
        user_history = user.get('reading_history', [])
        
        # Create message for personalized recommendations
        message_content = {
            "query": query,
            "user_preferences": user.get('preferences', {}),
            "user_history": user_history,
            "top_k": top_k
        }
        
        message = recommendation_system.suggestion_agent.send_message(
            recommendation_system.suggestion_agent.agent_id,
            "get_personalized_recommendations",
            message_content
        )
        
        response = recommendation_system.suggestion_agent.process_message(message)
        
        if response and response.message_type == "personalized_recommendation_result":
            return jsonify({
                "success": True,
                "recommendations": response.content["recommendations"],
                "personalization_score": response.content["personalization_score"],
                "preference_analysis": response.content["preference_analysis"]
            }), 200
        else:
            return jsonify({"error": "Failed to get personalized recommendations"}), 500
        
    except Exception as e:
        logger.error(f"Personalized recommendations error: {e}")
        return jsonify({"error": "Failed to get personalized recommendations"}), 500

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

@app.route('/api/books/search', methods=['POST'])
@jwt_required()
def search_books():
    """Search books using semantic search"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 10)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        # Perform semantic search
        message_content = {
            "query": query,
            "top_k": top_k
        }
        
        message = recommendation_system.suggestion_agent.send_message(
            recommendation_system.suggestion_agent.agent_id,
            "semantic_search",
            message_content
        )
        
        response = recommendation_system.suggestion_agent.process_message(message)
        
        if response and response.message_type == "semantic_search_result":
            return jsonify({
                "success": True,
                "results": response.content["results"],
                "total_results": response.content["total_results"]
            }), 200
        else:
            return jsonify({"error": "Search failed"}), 500
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

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

@app.route('/api/books/google-search', methods=['POST'])
@jwt_required()
def search_google_books():
    """Search Google Books directly (premium feature)"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        plan = user.get('plan', 'free')
        
        # Check if user has premium features
        if not PLAN_LIMITS[plan]['premium_features']:
            return jsonify({
                "error": "Premium feature - upgrade to Pro plan",
                "upgrade_required": True
            }), 403
        
        data = request.get_json()
        query = data.get('query', '')
        max_results = min(data.get('max_results', 10), 20)
        
        if not query:
            return jsonify({"error": "Query is required"}), 400
        
        if not enhanced_system:
            return jsonify({"error": "Google Books integration not available"}), 503
        
        # Search Google Books
        google_books = enhanced_system.search_google_books(query, max_results)
        
        return jsonify({
            "success": True,
            "results": google_books,
            "total_results": len(google_books),
            "source": "google_books",
            "premium_feature": True
        }), 200
        
    except Exception as e:
        logger.error(f"Google Books search error: {e}")
        return jsonify({"error": "Failed to search Google Books"}), 500

@app.route('/api/books/enhanced-details/<isbn>', methods=['GET'])
@jwt_required()
def get_enhanced_book_details(isbn):
    """Get enhanced book details from Google Books (premium feature)"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        plan = user.get('plan', 'free')
        
        # Check if user has premium features
        if not PLAN_LIMITS[plan]['premium_features']:
            return jsonify({
                "error": "Premium feature - upgrade to Pro plan",
                "upgrade_required": True
            }), 403
        
        if not enhanced_system:
            return jsonify({"error": "Google Books integration not available"}), 503
        
        # Get enhanced details
        book_details = enhanced_system.get_enhanced_book_details(isbn)
        
        if book_details:
            return jsonify({
                "success": True,
                "book": book_details,
                "source": "google_books",
                "premium_feature": True
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Book not found in Google Books"
            }), 404
        
    except Exception as e:
        logger.error(f"Enhanced book details error: {e}")
        return jsonify({"error": "Failed to get enhanced book details"}), 500

@app.route('/api/commercialization/book-links', methods=['POST'])
@jwt_required()
def get_book_purchase_links():
    """Get purchase links for books (premium feature)"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        plan = user.get('plan', 'free')
        
        # Check if user has premium features
        if not PLAN_LIMITS[plan]['premium_features']:
            return jsonify({
                "error": "Premium feature - upgrade to Pro plan",
                "upgrade_required": True
            }), 403
        
        data = request.get_json()
        isbn = data.get('isbn')
        
        if not isbn:
            return jsonify({"error": "ISBN is required"}), 400
        
        # This would integrate with book retailer APIs
        # For now, return mock data
        purchase_links = {
            "amazon": f"https://amazon.com/dp/{isbn}",
            "google_books": f"https://books.google.com/books?id={isbn}",
            "goodreads": f"https://goodreads.com/book/show/{isbn}",
            "local_library": f"https://worldcat.org/isbn/{isbn}"
        }
        
        return jsonify({
            "isbn": isbn,
            "purchase_links": purchase_links,
            "premium_feature": True
        }), 200
        
    except Exception as e:
        logger.error(f"Book links error: {e}")
        return jsonify({"error": "Failed to get purchase links"}), 500

@app.route('/api/transparency/user-report', methods=['GET'])
@jwt_required()
def get_user_transparency_report():
    """Get transparency report for the current user"""
    try:
        username = get_jwt_identity()
        report = transparency_reporter.generate_user_transparency_report(username)
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"User transparency report error: {e}")
        return jsonify({"error": "Failed to generate transparency report"}), 500

@app.route('/api/transparency/system-report', methods=['GET'])
@jwt_required()
def get_system_transparency_report():
    """Get system-wide transparency report (admin feature)"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        # Only allow pro users to access system reports
        if user.get('plan') != 'pro':
            return jsonify({
                "error": "System transparency reports are available for Pro users only",
                "upgrade_required": True
            }), 403
        
        report = transparency_reporter.generate_system_transparency_report()
        return jsonify(report), 200
        
    except Exception as e:
        logger.error(f"System transparency report error: {e}")
        return jsonify({"error": "Failed to generate system transparency report"}), 500

@app.route('/api/transparency/bias-analysis', methods=['GET'])
@jwt_required()
def get_bias_analysis():
    """Get bias analysis report"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        # Only allow pro users to access bias analysis
        if user.get('plan') != 'pro':
            return jsonify({
                "error": "Bias analysis is available for Pro users only",
                "upgrade_required": True
            }), 403
        
        days = request.args.get('days', 30, type=int)
        analysis = ethical_ai_monitor.analyze_bias_in_recommendations(days)
        return jsonify(analysis), 200
        
    except Exception as e:
        logger.error(f"Bias analysis error: {e}")
        return jsonify({"error": "Failed to generate bias analysis"}), 500

@app.route('/api/transparency/ethical-issues', methods=['GET'])
@jwt_required()
def get_ethical_issues():
    """Get detected ethical issues"""
    try:
        username = get_jwt_identity()
        user = users_db.get(username, {})
        
        # Only allow pro users to access ethical issues
        if user.get('plan') != 'pro':
            return jsonify({
                "error": "Ethical issues report is available for Pro users only",
                "upgrade_required": True
            }), 403
        
        issues = ethical_ai_monitor.detect_potential_issues()
        return jsonify({
            "issues": issues,
            "total_issues": len(issues),
            "report_generated_at": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Ethical issues error: {e}")
        return jsonify({"error": "Failed to get ethical issues"}), 500

if __name__ == '__main__':
    # Initialize the system
    books_path = "data/books_with_categories.csv"
    vector_db_path = "db_books"
    
    if recommendation_system.initialize_system(books_path, vector_db_path):
        # Initialize Google Books integration (optional)
        google_api_key = os.getenv('GOOGLE_BOOKS_API_KEY')
        if google_api_key:
            try:
                enhanced_system = create_enhanced_system(google_api_key)
                logger.info("Google Books integration initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Books integration: {e}")
                enhanced_system = None
        else:
            logger.info("Google Books API key not provided - running without Google Books integration")
            enhanced_system = None
        
        logger.info("Starting Book Sphere Multi-Agent API Server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    else:
        logger.error("Failed to initialize system")
