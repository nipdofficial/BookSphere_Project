# Book Sphere Startup Guide

## Prerequisites
- Python 3.11 (installed and working)
- Node.js and npm (for frontend)
- Virtual environment activated

## Quick Start

### 1. Backend Setup
```bash
# Navigate to project directory
cd "C:\Users\MSI\Desktop\Book Sphere - Copy"

# Activate virtual environment
.venv\Scripts\activate

# Start backend server
python start_backend.py
```

The backend will be available at: http://localhost:5000

### 2. Frontend Setup (in a new terminal)
```bash
# Navigate to project directory
cd "C:\Users\MSI\Desktop\Book Sphere - Copy"

# Run the frontend startup script
.\start_frontend.ps1
```

Or manually:
```bash
cd frontend
npm install
npm start
```

The frontend will be available at: http://localhost:3000

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Recommendations
- `POST /api/recommendations` - Get book recommendations (requires authentication)

### User Management
- `GET /api/user/preferences` - Get user preferences
- `POST /api/user/preferences` - Update user preferences

### Health Check
- `GET /api/health` - Check server health

## Testing the API

### Register a user:
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass","email":"test@example.com"}'
```

### Login:
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"testpass"}'
```

### Get recommendations (replace TOKEN with actual token):
```bash
curl -X POST http://localhost:5000/api/recommendations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{"query":"science fiction"}'
```

## Troubleshooting

### Backend Issues
- Make sure Python 3.11 is being used
- Ensure virtual environment is activated
- Check that all dependencies are installed

### Frontend Issues
- Make sure Node.js is installed
- Run `npm install` in the frontend directory
- Check that port 3000 is not in use

### Port Conflicts
- Backend uses port 5000
- Frontend uses port 3000
- Make sure these ports are available

## Features Available

### Current Features (Simplified Version)
- User registration and authentication
- Basic book recommendations (mock data)
- User preferences management
- JWT-based authentication
- CORS enabled for frontend communication

### Google Books Integration
- API key is configured
- Ready for enhanced book data integration

## Next Steps
1. Start both servers
2. Test the API endpoints
3. Access the frontend at http://localhost:3000
4. Register a user and test recommendations
