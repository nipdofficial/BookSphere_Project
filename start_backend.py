"""
Backend startup script for Book Sphere
This script handles the proper initialization and startup of the backend server
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """Setup environment variables and paths"""
    # Set Google Books API key
    os.environ['GOOGLE_BOOKS_API_KEY'] = 'AIzaSyBml4Xf5m4rCpr4x7dS45tv4Q3FTO8WOCE'
    
    # Set JWT secret key
    os.environ['JWT_SECRET_KEY'] = 'book-sphere-secret-key-2024'
    
    logger.info("Environment variables set")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import flask
        import flask_cors
        import flask_jwt_extended
        logger.info("Core Flask dependencies available")
        return True
    except ImportError as e:
        logger.error(f"Missing core dependencies: {e}")
        return False

def start_enhanced_server():
    """Start the enhanced server with full functionality"""
    try:
        from main_api_enhanced import app
        logger.info("Starting enhanced Book Sphere API server...")
        logger.info("Features: Semantic search, Google Books integration, Library management")
        logger.info("Server will be available at: http://localhost:5000")
        logger.info("API documentation available at: http://localhost:5000/")
        
        app.run(debug=True, host='0.0.0.0', port=5000)
        
    except Exception as e:
        logger.error(f"Failed to start enhanced server: {e}")
        logger.info("Falling back to simplified server...")
        try:
            from main_api_simple import app
            logger.info("Starting simplified Book Sphere API server...")
            app.run(debug=True, host='0.0.0.0', port=5000)
        except Exception as e2:
            logger.error(f"Failed to start simplified server: {e2}")
            return False

def main():
    """Main startup function"""
    logger.info("=" * 50)
    logger.info("Book Sphere Backend Startup")
    logger.info("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Dependency check failed. Please install required packages.")
        sys.exit(1)
    
    # Start server
    logger.info("Starting enhanced server...")
    start_enhanced_server()

if __name__ == "__main__":
    main()
