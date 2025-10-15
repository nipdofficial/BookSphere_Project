import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import BookModal from './BookModal';
import './BookCard.css';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:5000';

function BookCard({ book, onAddToLibrary }) {
  const [showModal, setShowModal] = useState(false);

  const handleCardClick = () => {
    setShowModal(true);
  };

  const renderStars = (rating) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < fullStars; i++) {
      stars.push(<span key={i} className="star">★</span>);
    }

    if (hasHalfStar) {
      stars.push(<span key="half" className="star">☆</span>);
    }

    const emptyStars = 5 - Math.ceil(rating);
    for (let i = 0; i < emptyStars; i++) {
      stars.push(<span key={`empty-${i}`} className="star empty">☆</span>);
    }

    return stars;
  };

  const getCoverImage = () => {
    // Try different thumbnail fields
    if (book.large_thumbnail && book.large_thumbnail !== 'cover-not-found.jpg' && !book.large_thumbnail.includes('cover-not-found')) {
      return book.large_thumbnail;
    }
    if (book.thumbnail && book.thumbnail !== 'cover-not-found.jpg' && !book.thumbnail.includes('cover-not-found')) {
      return book.thumbnail;
    }
    if (book.image_url && book.image_url !== 'cover-not-found.jpg' && !book.image_url.includes('cover-not-found')) {
      return book.image_url;
    }
    
    // Generate a placeholder with book title
    const title = encodeURIComponent(book.title || 'Book Cover');
    return `https://via.placeholder.com/200x300/4a5568/ffffff?text=${title.substring(0, 20)}`;
  };

  return (
    <>
      <div className="book-card" onClick={handleCardClick}>
        <div className="book-cover-container">
          <img 
            src={getCoverImage()} 
            alt={book.title}
            className="book-cover"
            onError={(e) => {
              const title = encodeURIComponent(book.title || 'Book Cover');
              e.target.src = `https://via.placeholder.com/200x300/4a5568/ffffff?text=${title.substring(0, 20)}`;
            }}
          />
          {book.popularity_score && (
            <div className="popularity-badge">
              Popularity: {Math.round(book.popularity_score * 100)}%
            </div>
          )}
        </div>

        <div className="book-info">
          <h3 className="book-title">{book.title}</h3>
          <p className="book-author">by {book.authors}</p>
          
          <div className="book-meta">
            <div className="book-rating">
              {renderStars(book.average_rating || 0)}
              <span className="rating-text">
                {book.average_rating ? book.average_rating.toFixed(1) : 'N/A'}
              </span>
            </div>
            <span className="book-category">{book.simple_categories}</span>
          </div>

          <p className="book-description">
            {book.description ? 
              book.description.substring(0, 150) + '...' : 
              'No description available'
            }
          </p>

          <div className="book-actions">
            <button 
              className="btn btn-primary btn-small"
              onClick={(e) => {
                e.stopPropagation();
                handleCardClick();
              }}
            >
              View Details
            </button>
          </div>
        </div>
      </div>

      <BookModal 
        book={book}
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        onAddToLibrary={onAddToLibrary}
      />
    </>
  );
}

export default BookCard;
