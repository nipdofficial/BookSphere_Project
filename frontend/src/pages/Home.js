import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import './Home.css';

function Home() {
  const { user } = useAuth();

  return (
    <div className="home">
      <div className="hero">
        <div className="container">
          <h1>Discover Your Next Favorite Book</h1>
          <p>AI-powered book recommendations tailored just for you</p>
          
          {user ? (
            <Link to="/dashboard" className="btn btn-primary btn-large">
              Start Exploring
            </Link>
          ) : (
            <div className="hero-actions">
              <Link to="/register" className="btn btn-primary btn-large">
                Get Started Free
              </Link>
              <Link to="/login" className="btn btn-secondary btn-large">
                Sign In
              </Link>
            </div>
          )}
        </div>
      </div>

      <div className="features-section">
        <div className="container">
          <h2>Why Choose Book Sphere?</h2>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3>AI-Powered Recommendations</h3>
              <p>Our multi-agent AI system analyzes your preferences and finds books you'll love</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🎯</div>
              <h3>Personalized Search</h3>
              <p>Get recommendations based on your reading history and emotional preferences</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">📊</div>
              <h3>Smart Analytics</h3>
              <p>Track your reading habits and discover trending books in your favorite genres</p>
            </div>
            
            <div className="feature-card">
              <div className="feature-icon">🛒</div>
              <h3>Easy Purchase</h3>
              <p>Find where to buy books with direct links to major retailers and libraries</p>
            </div>
          </div>
        </div>
      </div>

      <div className="how-it-works">
        <div className="container">
          <h2>How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <h3>Describe What You Want</h3>
              <p>Tell us what kind of book you're looking for - our AI understands natural language</p>
            </div>
            
            <div className="step">
              <div className="step-number">2</div>
              <h3>AI Agents Work Together</h3>
              <p>Our classification, popularity, and suggestion agents collaborate to find perfect matches</p>
            </div>
            
            <div className="step">
              <div className="step-number">3</div>
              <h3>Get Personalized Results</h3>
              <p>Receive recommendations tailored to your preferences and reading history</p>
            </div>
          </div>
        </div>
      </div>

      <div className="pricing-section">
        <div className="container">
          <h2>Simple Pricing</h2>
          <div className="pricing-grid">
            <div className="pricing-card free">
              <h3>Free Plan</h3>
              <div className="price">$0<span>/month</span></div>
              <ul className="features-list">
                <li>✓ Basic book recommendations</li>
                <li>✓ Category and emotion filtering</li>
                <li>✓ Reading history tracking</li>
                <li>✓ Up to 10 recommendations per search</li>
              </ul>
              <Link to="/register" className="btn btn-outline">
                Get Started
              </Link>
            </div>
            
            <div className="pricing-card premium">
              <div className="premium-badge">Most Popular</div>
              <h3>Premium Plan</h3>
              <div className="price">$9.99<span>/month</span></div>
              <ul className="features-list">
                <li>✓ Everything in Free Plan</li>
                <li>✓ Personalized AI recommendations</li>
                <li>✓ Purchase links to retailers</li>
                <li>✓ Advanced analytics</li>
                <li>✓ Priority support</li>
                <li>✓ Unlimited recommendations</li>
              </ul>
              <Link to="/register" className="btn btn-primary">
                Upgrade Now
              </Link>
            </div>
          </div>
        </div>
      </div>

      <div className="cta-section">
        <div className="container">
          <h2>Ready to Discover Amazing Books?</h2>
          <p>Join thousands of readers who have found their next favorite book with Book Sphere</p>
          {!user && (
            <Link to="/register" className="btn btn-primary btn-large">
              Start Your Journey
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}

export default Home;
