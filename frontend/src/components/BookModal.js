import React from 'react';
import { toast } from 'react-toastify';
import axios from 'axios';
import './BookModal.css';

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:5000';

function BookModal({ book, isOpen, onClose, onAddToLibrary }) {
  const [showPurchaseLinks, setShowPurchaseLinks] = React.useState(false);
  const [purchaseLinks, setPurchaseLinks] = React.useState(null);
  const [loadingLinks, setLoadingLinks] = React.useState(false);

  const handleAddToLibrary = async () => {
    try {
      const response = await axios.post('/api/user/library', {
        isbn13: book.isbn13,
        isbn10: book.isbn10,
        title: book.title,
        authors: book.authors,
        simple_categories: book.simple_categories,
        average_rating: book.average_rating,
        description: book.description,
        thumbnail: book.thumbnail,
        large_thumbnail: book.large_thumbnail
      });
      
      if (response.status === 429) {
        toast.error(response.data.error);
        if (response.data.upgrade_required) {
          // Could trigger upgrade modal here
        }
      } else {
        toast.success('Added to your library!');
        if (onAddToLibrary) {
          onAddToLibrary(book);
        }
      }
    } catch (error) {
      if (error.response?.status === 429) {
        toast.error(error.response.data.error);
      } else if (error.response?.status === 400) {
        toast.error(error.response.data.error);
      } else {
        toast.error('Failed to add to library');
      }
    }
  };

  const handleGetPurchaseLinks = async () => {
    if (purchaseLinks) {
      setShowPurchaseLinks(!showPurchaseLinks);
      return;
    }

    setLoadingLinks(true);
    try {
      // Use Google Books links directly from the book data
      const links = {
        google_books: book.preview_link || book.info_link || book.canonical_volume_link,
        amazon: `https://www.amazon.com/s?k=${encodeURIComponent(book.title + ' ' + book.authors)}`,
        goodreads: `https://www.goodreads.com/search?q=${encodeURIComponent(book.title + ' ' + book.authors)}`,
        local_library: `https://www.worldcat.org/search?q=${encodeURIComponent(book.title + ' ' + book.authors)}`
      };
      
      setPurchaseLinks(links);
      setShowPurchaseLinks(true);
    } catch (error) {
      toast.error('Failed to get purchase links');
    } finally {
      setLoadingLinks(false);
    }
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
    return `https://via.placeholder.com/300x450/4a5568/ffffff?text=${title.substring(0, 20)}`;
  };

  if (!isOpen || !book) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>×</button>
        
        <div className="modal-body">
          <div className="book-modal-cover">
            <img 
              src={getCoverImage()} 
              alt={book.title}
              className="book-modal-image"
              onError={(e) => {
                const title = encodeURIComponent(book.title || 'Book Cover');
                e.target.src = `https://via.placeholder.com/300x450/4a5568/ffffff?text=${title.substring(0, 20)}`;
              }}
            />
          </div>
          
          <div className="book-modal-info">
            <h2 className="book-modal-title">{book.title}</h2>
            <p className="book-modal-author">by {book.authors}</p>
            
            <div className="book-modal-meta">
              <div className="book-modal-rating">
                {renderStars(book.average_rating || 0)}
                <span className="rating-text">
                  {book.average_rating ? book.average_rating.toFixed(1) : 'N/A'}
                </span>
                <span className="ratings-count">
                  ({book.ratings_count || 0} ratings)
                </span>
              </div>
              <div className="book-modal-category">{book.simple_categories}</div>
            </div>

            <div className="book-modal-details">
              <div className="detail-item">
                <strong>Published:</strong> {book.published_year || 'N/A'}
              </div>
              <div className="detail-item">
                <strong>Pages:</strong> {book.num_pages || 'N/A'}
              </div>
              <div className="detail-item">
                <strong>ISBN:</strong> {book.isbn13 || book.isbn10 || 'N/A'}
              </div>
              {book.popularity_score && (
                <div className="detail-item">
                  <strong>Popularity Score:</strong> {Math.round(book.popularity_score * 100)}%
                </div>
              )}
            </div>

            <div className="book-modal-description">
              <h3>Description</h3>
              <p>
                {book.description || book.tagged_description || 'No description available'}
              </p>
            </div>

            <div className="book-modal-actions">
              <button 
                onClick={handleAddToLibrary}
                className="btn btn-primary"
              >
                Add to My Library
              </button>
              
              <button 
                onClick={handleGetPurchaseLinks}
                className="btn btn-secondary"
                disabled={loadingLinks}
              >
                {loadingLinks ? 'Loading...' : 'Find Book Online'}
              </button>
            </div>

            {showPurchaseLinks && purchaseLinks && (
              <div className="purchase-links-modal">
                <h4>Where to Buy:</h4>
                <div className="links-grid-modal">
                  <a 
                    href={purchaseLinks.amazon} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="purchase-link amazon"
                  >
                    Amazon
                  </a>
                  <a 
                    href={purchaseLinks.google_books} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="purchase-link google"
                  >
                    Google Books
                  </a>
                  <a 
                    href={purchaseLinks.goodreads} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="purchase-link goodreads"
                  >
                    Goodreads
                  </a>
                  <a 
                    href={purchaseLinks.local_library} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="purchase-link library"
                  >
                    Find Library
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookModal;
