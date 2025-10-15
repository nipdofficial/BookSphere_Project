import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import BookCard from '../components/BookCard';
import './Dashboard.css';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:5000';

function Dashboard() {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState({
    category: 'All',
    emotion_tone: 'All',
    min_rating: 0
  });
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchType, setSearchType] = useState('general'); // 'general' or 'personalized'
  const [planInfo, setPlanInfo] = useState(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) {
      toast.error('Please enter a search query');
      return;
    }

    setLoading(true);
    try {
      let response;
      
      if (searchType === 'personalized') {
        response = await axios.post('/api/recommendations/personalized', {
          query,
          top_k: 20
        });
      } else {
        response = await axios.post('/api/recommendations', {
          query,
          category: filters.category,
          tone: filters.emotion_tone,
          top_k: 20
        });
      }

      if (response.data.success) {
        setRecommendations(response.data.recommendations);
        setPlanInfo(response.data);
        toast.success(`Found ${response.data.recommendations.length} recommendations`);
      } else {
        toast.error('Failed to get recommendations');
      }
    } catch (error) {
      if (error.response?.status === 429) {
        toast.error(error.response.data.error);
        if (error.response.data.upgrade_required) {
          setShowUpgradeModal(true);
        }
      } else {
        toast.error('Error getting recommendations');
      }
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };

  const handleUpgrade = async () => {
    try {
      const response = await axios.post('/api/user/upgrade');
      toast.success(response.data.message);
      setPlanInfo(prev => ({ ...prev, plan: 'pro' }));
      setShowUpgradeModal(false);
    } catch (error) {
      toast.error('Failed to upgrade plan');
    }
  };

  const categories = [
    'All', 'Fiction', 'Nonfiction', "Children's Fiction", 
    "Children's Nonfiction", 'Other'
  ];

  const emotionTones = [
    'All', 'Happy', 'Sad', 'Angry', 'Suspenseful', 'Surprising'
  ];

  return (
    <div className="dashboard">
      <div className="container">
        <div className="dashboard-header">
          <h1>Book Recommendations</h1>
          <p>Discover your next favorite book with AI-powered recommendations</p>
          
          {planInfo && (
            <div className="plan-status">
              <div className="plan-badge">
                {planInfo.plan === 'pro' ? '⭐ Pro Plan' : '🆓 Free Plan'}
              </div>
              <div className="usage-info">
                <span>Daily: {planInfo.usage?.daily_searches || 0}/{planInfo.plan === 'pro' ? '100' : '5'}</span>
                <span>Monthly: {planInfo.usage?.monthly_searches || 0}/{planInfo.plan === 'pro' ? '2000' : '50'}</span>
              </div>
              {planInfo.plan === 'free' && (
                <button 
                  className="upgrade-btn-small"
                  onClick={() => setShowUpgradeModal(true)}
                >
                  Upgrade to Pro
                </button>
              )}
            </div>
          )}
        </div>

        <div className="search-section">
          <div className="search-type-toggle">
            <button 
              className={`toggle-btn ${searchType === 'general' ? 'active' : ''}`}
              onClick={() => setSearchType('general')}
            >
              General Search
            </button>
            <button 
              className={`toggle-btn ${searchType === 'personalized' ? 'active' : ''}`}
              onClick={() => setSearchType('personalized')}
            >
              Personalized Search
            </button>
          </div>

          <div className="search-form">
            <div className="search-input">
              <input
                type="text"
                placeholder="Describe what kind of book you're looking for..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="form-input"
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <button 
              onClick={handleSearch}
              className="btn btn-primary"
              disabled={loading}
            >
              {loading ? 'Searching...' : 'Find Books'}
            </button>
          </div>

          {searchType === 'general' && (
            <div className="filters">
              <div className="form-group">
                <label className="form-label">Category</label>
                <select
                  value={filters.category}
                  onChange={(e) => handleFilterChange('category', e.target.value)}
                  className="form-select"
                >
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Emotional Tone</label>
                <select
                  value={filters.emotion_tone}
                  onChange={(e) => handleFilterChange('emotion_tone', e.target.value)}
                  className="form-select"
                >
                  {emotionTones.map(tone => (
                    <option key={tone} value={tone}>{tone}</option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Minimum Rating</label>
                <select
                  value={filters.min_rating}
                  onChange={(e) => handleFilterChange('min_rating', parseFloat(e.target.value))}
                  className="form-select"
                >
                  <option value={0}>Any Rating</option>
                  <option value={3.0}>3.0+ Stars</option>
                  <option value={3.5}>3.5+ Stars</option>
                  <option value={4.0}>4.0+ Stars</option>
                  <option value={4.5}>4.5+ Stars</option>
                </select>
              </div>
            </div>
          )}

          {searchType === 'personalized' && (
            <div className="personalized-info">
              <p>✨ Personalized search uses your reading history and preferences to find books tailored just for you!</p>
            </div>
          )}
        </div>

        {loading && (
          <div className="loading">
            <div className="spinner"></div>
            <p>Our AI agents are working to find the perfect books for you...</p>
          </div>
        )}

        {recommendations.length > 0 && (
          <div className="results-section">
            <h2>Recommended Books</h2>
            <div className="book-grid">
              {recommendations.map((book, index) => (
                <BookCard key={book.isbn13 || index} book={book} />
              ))}
            </div>
          </div>
        )}

        {!loading && recommendations.length === 0 && query && (
          <div className="no-results">
            <h3>No books found</h3>
            <p>Try adjusting your search query or filters</p>
          </div>
        )}
      </div>

      {showUpgradeModal && (
        <div className="modal-overlay" onClick={() => setShowUpgradeModal(false)}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowUpgradeModal(false)}>×</button>
            <div className="upgrade-content">
              <h2>Upgrade to Pro Plan</h2>
              <div className="upgrade-features">
                <div className="feature">
                  <span className="feature-icon">🔍</span>
                  <div>
                    <h4>Unlimited Searches</h4>
                    <p>100 daily searches, 2000 monthly searches</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">📚</span>
                  <div>
                    <h4>Large Library</h4>
                    <p>Save up to 1000 books in your library</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">🛒</span>
                  <div>
                    <h4>Purchase Links</h4>
                    <p>Get direct links to buy books from multiple retailers</p>
                  </div>
                </div>
                <div className="feature">
                  <span className="feature-icon">⚡</span>
                  <div>
                    <h4>Priority Support</h4>
                    <p>Faster response times and priority assistance</p>
                  </div>
                </div>
              </div>
              <div className="upgrade-actions">
                <button className="btn btn-secondary" onClick={() => setShowUpgradeModal(false)}>
                  Maybe Later
                </button>
                <button className="btn btn-primary" onClick={handleUpgrade}>
                  Upgrade Now (Free Trial)
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
