import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import { useAuth } from '../contexts/AuthContext';
import './Profile.css';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:5000';

function Profile() {
  const { user } = useAuth();
  const [preferences, setPreferences] = useState({
    preferred_genres: [],
    min_rating: 3.0,
    reading_goals: '',
    favorite_authors: []
  });
  const [readingHistory, setReadingHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    try {
      const response = await axios.get('/api/user/preferences');
      setPreferences(response.data.preferences);
      setReadingHistory(response.data.reading_history);
    } catch (error) {
      toast.error('Failed to load user data');
    } finally {
      setLoading(false);
    }
  };

  const handlePreferenceUpdate = async (updatedPreferences) => {
    try {
      await axios.post('/api/user/preferences', updatedPreferences);
      setPreferences(updatedPreferences);
      toast.success('Preferences updated successfully!');
    } catch (error) {
      toast.error('Failed to update preferences');
    }
  };

  const handleGenreToggle = (genre) => {
    const updatedGenres = preferences.preferred_genres.includes(genre)
      ? preferences.preferred_genres.filter(g => g !== genre)
      : [...preferences.preferred_genres, genre];
    
    handlePreferenceUpdate({
      ...preferences,
      preferred_genres: updatedGenres
    });
  };

  const handleRatingChange = (rating) => {
    handlePreferenceUpdate({
      ...preferences,
      min_rating: rating
    });
  };

  const availableGenres = [
    'Fiction', 'Nonfiction', "Children's Fiction", 
    "Children's Nonfiction", 'Mystery', 'Romance', 
    'Science Fiction', 'Fantasy', 'Biography'
  ];

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div className="profile">
      <div className="container">
        <div className="profile-header">
          <h1>Your Profile</h1>
          <p>Manage your reading preferences and view your history</p>
        </div>

        <div className="profile-content">
          <div className="profile-section">
            <h2>Reading Preferences</h2>
            <div className="preferences-card">
              <div className="preference-group">
                <h3>Preferred Genres</h3>
                <div className="genre-tags">
                  {availableGenres.map(genre => (
                    <button
                      key={genre}
                      className={`genre-tag ${preferences.preferred_genres.includes(genre) ? 'active' : ''}`}
                      onClick={() => handleGenreToggle(genre)}
                    >
                      {genre}
                    </button>
                  ))}
                </div>
              </div>

              <div className="preference-group">
                <h3>Minimum Rating Preference</h3>
                <div className="rating-slider">
                  <input
                    type="range"
                    min="1"
                    max="5"
                    step="0.5"
                    value={preferences.min_rating}
                    onChange={(e) => handleRatingChange(parseFloat(e.target.value))}
                    className="slider"
                  />
                  <span className="rating-display">{preferences.min_rating} stars</span>
                </div>
              </div>

              <div className="preference-group">
                <h3>Reading Goals</h3>
                <textarea
                  value={preferences.reading_goals}
                  onChange={(e) => handlePreferenceUpdate({
                    ...preferences,
                    reading_goals: e.target.value
                  })}
                  placeholder="What are your reading goals for this year?"
                  className="goals-textarea"
                />
              </div>
            </div>
          </div>

          <div className="profile-section">
            <h2>Reading History</h2>
            <div className="history-card">
              {readingHistory.length > 0 ? (
                <div className="history-list">
                  {readingHistory.map((book, index) => (
                    <div key={index} className="history-item">
                      <div className="history-book-info">
                        <h4>{book.title}</h4>
                        <p>by {book.authors}</p>
                        <span className="history-category">{book.simple_categories}</span>
                      </div>
                      <div className="history-meta">
                        <div className="history-rating">
                          {Array.from({ length: 5 }, (_, i) => (
                            <span 
                              key={i} 
                              className={`star ${i < Math.floor(book.average_rating) ? 'filled' : ''}`}
                            >
                              ★
                            </span>
                          ))}
                        </div>
                        <span className="history-date">
                          Added: {new Date(book.added_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="no-history">
                  <p>No books in your reading history yet.</p>
                  <p>Start exploring and add books to your history!</p>
                </div>
              )}
            </div>
          </div>

          <div className="profile-section">
            <h2>Account Information</h2>
            <div className="account-card">
              <div className="account-info">
                <div className="info-item">
                  <label>Username:</label>
                  <span>{user.username}</span>
                </div>
                <div className="info-item">
                  <label>Email:</label>
                  <span>{user.email}</span>
                </div>
                <div className="info-item">
                  <label>Member Since:</label>
                  <span>{new Date().toLocaleDateString()}</span>
                </div>
                <div className="info-item">
                  <label>Books in History:</label>
                  <span>{readingHistory.length}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Profile;
