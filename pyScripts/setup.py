#!/usr/bin/env python3
"""
Book Sphere Multi-Agent System Setup Script
Automates the installation and configuration process
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def setup_backend():
    """Setup the backend environment"""
    print("\n🚀 Setting up backend...")
    
    # Create virtual environment
    if not run_command("python -m venv venv", "Creating virtual environment"):
        return False
    
    # Determine activation script based on OS
    if os.name == 'nt':  # Windows
        activate_script = "venv\\Scripts\\activate"
        pip_command = "venv\\Scripts\\pip"
    else:  # Unix/Linux/MacOS
        activate_script = "source venv/bin/activate"
        pip_command = "venv/bin/pip"
    
    # Install requirements
    if not run_command(f"{pip_command} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_command} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    print("✅ Backend setup completed")
    return True

def setup_frontend():
    """Setup the frontend environment"""
    print("\n🎨 Setting up frontend...")
    
    # Check if Node.js is installed
    if not run_command("node --version", "Checking Node.js installation"):
        print("❌ Node.js is not installed. Please install Node.js 16+ from https://nodejs.org/")
        return False
    
    # Check if npm is installed
    if not run_command("npm --version", "Checking npm installation"):
        print("❌ npm is not installed. Please install npm")
        return False
    
    # Navigate to frontend directory
    frontend_path = Path("../frontend")
    if not frontend_path.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install frontend dependencies
    if not run_command("cd frontend && npm install", "Installing frontend dependencies"):
        return False
    
    print("✅ Frontend setup completed")
    return True

def create_env_file():
    """Create environment configuration file"""
    print("\n⚙️ Creating environment configuration...")
    
    env_content = """# Book Sphere Environment Configuration
# JWT Secret Key (change in production)
JWT_SECRET_KEY=your-secret-key-change-in-production-$(date +%s)

# Optional: Groq API Key for enhanced features
# GROQ_API_KEY=your-groq-api-key

# Optional: OpenAI API Key
# OPENAI_API_KEY=your-openai-api-key

# Database Configuration
DATABASE_URL=sqlite:///book_sphere.db

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# API Configuration
API_HOST=0.0.0.0
API_PORT=5000

# Frontend Configuration
REACT_APP_API_URL=http://localhost:5000
"""
    
    try:
        with open("../.env", "w") as f:
            f.write(env_content)
        print("✅ Environment file created (.env)")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def check_data_files():
    """Check if required data files exist"""
    print("\n📊 Checking data files...")
    
    required_files = [
        "data/books_cleaned.csv",
        "data/books_with_categories.csv", 
        "data/books_with_emotions.csv"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required data files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        print("\n📝 Please ensure all data files are present before running the system")
        return False
    
    print("✅ All required data files found")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = [
        "db_books",
        "logs",
        "uploads",
        "static/images"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Directories created")
    return True

def run_tests():
    """Run basic system tests"""
    print("\n🧪 Running system tests...")
    
    # Test Python imports
    test_script = """
import sys
sys.path.append('.')

try:
    from agents.base_agent import BaseAgent, AgentCommunicationHub
    from agents.classification_agent import ClassificationAgent
    from agents.popularity_agent import PopularityAnalyzerAgent
    from agents.suggestion_agent import SuggestionAgent
    print("✅ All agent imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run([sys.executable, "-c", test_script], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e.stderr}")
        return False

def print_next_steps():
    """Print instructions for next steps"""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next Steps:")
    print("1. Start the backend server:")
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
    else:  # Unix/Linux/MacOS
        print("   source venv/bin/activate")
    print("   python main_api.py")
    
    print("\n2. Start the frontend server (in a new terminal):")
    print("   cd frontend")
    print("   npm start")
    
    print("\n3. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend API: http://localhost:5000")
    
    print("\n4. Test the system:")
    print("   - Register a new account")
    print("   - Try searching for books")
    print("   - Check the API health endpoint: http://localhost:5000/api/health")
    
    print("\n📚 Documentation:")
    print("   - README.md: Complete project overview")
    print("   - COMMERCIALIZATION_PLAN.md: Business strategy")
    print("   - requirements.txt: Python dependencies")
    
    print("\n🆘 Need help?")
    print("   - Check the README.md for detailed instructions")
    print("   - Review the API documentation in main_api.py")
    print("   - Check the logs for any error messages")

def main():
    """Main setup function"""
    print("🚀 Book Sphere Multi-Agent System Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        print("❌ Backend setup failed")
        sys.exit(1)
    
    # Setup frontend
    if not setup_frontend():
        print("❌ Frontend setup failed")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Check data files
    if not check_data_files():
        print("⚠️ Data files missing - system may not work properly")
    
    # Run tests
    if not run_tests():
        print("⚠️ Some tests failed - check the error messages above")
    
    # Print next steps
    print_next_steps()

if __name__ == "__main__":
    main()
