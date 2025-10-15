import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="navbar">
      <div className="container">
        <div className="navbar-content">
          <Link to="/" className="logo">
            📚 Book Sphere
          </Link>
          
          <div className="nav-links">
            <Link to="/" className="nav-link">Home</Link>
            
            {user ? (
              <>
                <Link to="/dashboard" className="nav-link">Dashboard</Link>
                <Link to="/library" className="nav-link">My Library</Link>
                <div className="user-menu">
                  <span>Welcome, {user.username}</span>
                  <button onClick={handleLogout} className="btn btn-secondary btn-small">
                    Logout
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link to="/login" className="nav-link">Login</Link>
                <Link to="/register" className="btn btn-primary btn-small">
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
