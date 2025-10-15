import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import BookCard from '../components/BookCard';
import BookModal from '../components/BookModal';
import './MyLibrary.css';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:5000';

function MyLibrary() {
  const [library, setLibrary] = useState([]);
  const [planInfo, setPlanInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedBook, setSelectedBook] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [upgradeModal, setUpgradeModal] = useState(false);

  useEffect(() => {
    fetchLibrary();
    fetchPlanInfo();
  }, []);

  const fetchLibrary = async () => {
    try {
      const response = await axios.get('/api/user/library');
      setLibrary(response.data.library);
    } catch (error) {
      toast.error('Failed to load library');
      console.error('Library fetch error:', error);
    }
  };

  const fetchPlanInfo = async () => {
    try {
      const response = await axios.get('/api/user/plan');
      setPlanInfo(response.data);
    } catch (error) {
      console.error('Plan info fetch error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveFromLibrary = async (bookId) => {
    try {
      await axios.delete(`/api/user/library/${bookId}`);
      setLibrary(library.filter(book => 
        book.isbn13 !== bookId && book.isbn10 !== bookId
      ));
      toast.success('Book removed from library');
    } catch (error) {
      toast.error('Failed to remove book from library');
    }
  };

  const handleUpgrade = async () => {
    try {
      const response = await axios.post('/api/user/upgrade');
      toast.success(response.data.message);
      fetchPlanInfo();
      setUpgradeModal(false);
    } catch (error) {
      toast.error('Failed to upgrade plan');
    }
  };

  const handleBookClick = (book) => {
    setSelectedBook(book);
    setShowModal(true);
  };

  const handleAddToLibrary = (book) => {
    // Book is already in library, just refresh
    fetchLibrary();
  };

  if (loading) {
    return (
      <div className="library-loading">
        <div className="spinner"></div>
        <p>Loading your library...</p>
      </div>
    );
  }

  return (
    <div className="my-library">
      <div className="container">
        <div className="library-header">
          <h1>My Library</h1>
          <p>Your personal collection of recommended books</p>
        </div>

        {planInfo && (
          <div className="plan-info">
            <div className="plan-card">
              <div className="plan-header">
                <h3>Current Plan: {planInfo.plan.toUpperCase()}</h3>
                {planInfo.plan === 'free' && (
                  <button 
                    className="upgrade-btn"
                    onClick={() => setUpgradeModal(true)}
                  >
                    Upgrade to Pro
                  </button>
                )}
              </div>
              
              <div className="usage-stats">
                <div className="stat-item">
                  <span className="stat-label">Daily Searches</span>
                  <span className="stat-value">
                    {planInfo.usage.daily_searches || 0} / {planInfo.limits.daily_searches}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Monthly Searches</span>
                  <span className="stat-value">
                    {planInfo.usage.monthly_searches || 0} / {planInfo.limits.monthly_searches}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Library Books</span>
                  <span className="stat-value">
                    {planInfo.library_count} / {planInfo.library_limit}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div className="library-content">
          {library.length > 0 ? (
            <>
              <div className="library-stats">
                <h2>{library.length} Books in Your Library</h2>
                <p>Click on any book to view details or remove from library</p>
              </div>
              
              <div className="library-grid">
                {library.map((book, index) => (
                  <div key={book.isbn13 || book.isbn10 || index} className="library-book-card">
                    <BookCard 
                      book={book} 
                      onAddToLibrary={handleAddToLibrary}
                    />
                    <button 
                      className="remove-btn"
                      onClick={() => handleRemoveFromLibrary(book.isbn13 || book.isbn10)}
                      title="Remove from library"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div className="empty-library">
              <div className="empty-icon">📚</div>
              <h2>Your library is empty</h2>
              <p>Start exploring books and add them to your library to see them here!</p>
              <button 
                className="btn btn-primary"
                onClick={() => window.location.href = '/dashboard'}
              >
                Find Books
              </button>
            </div>
          )}
        </div>
      </div>

      {showModal && selectedBook && (
        <BookModal 
          book={selectedBook}
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          onAddToLibrary={handleAddToLibrary}
        />
      )}

      {upgradeModal && (
        <div className="modal-overlay" onClick={() => setUpgradeModal(false)}>
          <div className="upgrade-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setUpgradeModal(false)}>×</button>
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
                <button className="btn btn-secondary" onClick={() => setUpgradeModal(false)}>
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

export default MyLibrary;
