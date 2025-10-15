"""
Google Books API Integration
Enhances the existing dataset with Google Books data
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleBooksAPI:
    """Google Books API integration class"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/books/v1"
        self.rate_limit_delay = 0.1  # 100ms between requests to respect rate limits
        
    def search_books(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for books using Google Books API"""
        try:
            params = {
                'q': query,
                'maxResults': min(max_results, 40),  # Google Books API limit
                'fields': 'items(id,volumeInfo(title,authors,description,publishedDate,pageCount,ratingsCount,averageRating,categories,imageLinks,industryIdentifiers))'
            }
            
            if self.api_key:
                params['key'] = self.api_key
            
            response = requests.get(f"{self.base_url}/volumes", params=params)
            response.raise_for_status()
            
            data = response.json()
            books = []
            
            if 'items' in data:
                for item in data['items']:
                    book_info = self._parse_book_data(item)
                    if book_info:
                        books.append(book_info)
            
            # Respect rate limits
            time.sleep(self.rate_limit_delay)
            
            return books
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Books API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error processing Google Books response: {e}")
            return []
    
    def get_book_by_isbn(self, isbn: str) -> Optional[Dict[str, Any]]:
        """Get book details by ISBN"""
        try:
            # Try both ISBN-10 and ISBN-13 formats
            isbn_queries = [f"isbn:{isbn}"]
            
            # If it's a 13-digit ISBN, also try the 10-digit version
            if len(isbn) == 13 and isbn.startswith('978'):
                isbn_10 = self._convert_isbn13_to_isbn10(isbn)
                if isbn_10:
                    isbn_queries.append(f"isbn:{isbn_10}")
            
            for query in isbn_queries:
                books = self.search_books(query, max_results=1)
                if books:
                    return books[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting book by ISBN {isbn}: {e}")
            return None
    
    def _parse_book_data(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Google Books API response into our format"""
        try:
            volume_info = item.get('volumeInfo', {})
            
            # Extract ISBNs
            isbn13 = None
            isbn10 = None
            
            for identifier in volume_info.get('industryIdentifiers', []):
                if identifier.get('type') == 'ISBN_13':
                    isbn13 = identifier.get('identifier')
                elif identifier.get('type') == 'ISBN_10':
                    isbn10 = identifier.get('identifier')
            
            # Skip if no ISBN
            if not isbn13 and not isbn10:
                return None
            
            # Extract image links
            image_links = volume_info.get('imageLinks', {})
            thumbnail = image_links.get('thumbnail', '')
            large_thumbnail = image_links.get('large', '') or image_links.get('medium', '') or thumbnail
            
            # Clean up image URLs
            if thumbnail:
                thumbnail = thumbnail.replace('&edge=curl', '').replace('&zoom=1', '')
            if large_thumbnail:
                large_thumbnail = large_thumbnail.replace('&edge=curl', '').replace('&zoom=1', '')
            
            book_data = {
                'isbn13': isbn13,
                'isbn10': isbn10,
                'title': volume_info.get('title', ''),
                'authors': ', '.join(volume_info.get('authors', [])),
                'description': volume_info.get('description', ''),
                'published_year': self._extract_year(volume_info.get('publishedDate', '')),
                'num_pages': volume_info.get('pageCount'),
                'average_rating': volume_info.get('averageRating'),
                'ratings_count': volume_info.get('ratingsCount'),
                'categories': ', '.join(volume_info.get('categories', [])),
                'thumbnail': thumbnail,
                'large_thumbnail': large_thumbnail,
                'google_books_id': item.get('id'),
                'source': 'google_books'
            }
            
            return book_data
            
        except Exception as e:
            logger.error(f"Error parsing book data: {e}")
            return None
    
    def _extract_year(self, date_str: str) -> Optional[float]:
        """Extract year from date string"""
        try:
            if not date_str:
                return None
            
            # Try to extract year from various date formats
            import re
            year_match = re.search(r'(\d{4})', date_str)
            if year_match:
                return float(year_match.group(1))
            
            return None
        except:
            return None
    
    def _convert_isbn13_to_isbn10(self, isbn13: str) -> Optional[str]:
        """Convert ISBN-13 to ISBN-10"""
        try:
            if len(isbn13) != 13 or not isbn13.startswith('978'):
                return None
            
            # Remove the 978 prefix and last digit
            isbn10_base = isbn13[3:12]
            
            # Calculate check digit
            check_sum = sum(int(digit) * (10 - i) for i, digit in enumerate(isbn10_base))
            check_digit = (11 - (check_sum % 11)) % 11
            
            if check_digit == 10:
                check_digit = 'X'
            
            return isbn10_base + str(check_digit)
            
        except:
            return None

class EnhancedBookRecommendationSystem:
    """Enhanced system that combines local dataset with Google Books API"""
    
    def __init__(self, google_books_api: GoogleBooksAPI):
        self.google_books_api = google_books_api
        self.local_books_df = None
        self.vector_db = None
        
    def enhance_recommendations(self, local_recommendations: List[Dict[str, Any]], 
                              query: str) -> List[Dict[str, Any]]:
        """Enhance local recommendations with Google Books data"""
        enhanced_recommendations = []
        
        # First, add local recommendations
        for book in local_recommendations:
            enhanced_book = book.copy()
            enhanced_book['source'] = 'local_dataset'
            enhanced_recommendations.append(enhanced_book)
        
        # Then, search Google Books for additional results
        try:
            google_books = self.google_books_api.search_books(query, max_results=5)
            
            for google_book in google_books:
                # Check if this book is already in local recommendations
                is_duplicate = False
                for local_book in local_recommendations:
                    if (google_book.get('isbn13') and local_book.get('isbn13') == google_book['isbn13']) or \
                       (google_book.get('isbn10') and local_book.get('isbn10') == google_book['isbn10']):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    enhanced_recommendations.append(google_book)
            
        except Exception as e:
            logger.error(f"Error enhancing recommendations with Google Books: {e}")
        
        return enhanced_recommendations
    
    def get_enhanced_book_details(self, isbn: str) -> Optional[Dict[str, Any]]:
        """Get enhanced book details from Google Books"""
        return self.google_books_api.get_book_by_isbn(isbn)
    
    def search_google_books(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Google Books directly"""
        return self.google_books_api.search_books(query, max_results)

# Integration with main API
def create_enhanced_system(google_api_key: Optional[str] = None):
    """Create enhanced recommendation system with Google Books integration"""
    google_books_api = GoogleBooksAPI(api_key=google_api_key)
    return EnhancedBookRecommendationSystem(google_books_api)

# Example usage
if __name__ == "__main__":
    # Initialize with API key (optional)
    api_key = "AIzaSyBml4Xf5m4rCpr4x7dS45tv4Q3FTO8WOCE"  # Google Books API key
    
    google_api = GoogleBooksAPI(api_key=api_key)
    
    # Test search
    results = google_api.search_books("machine learning", max_results=5)
    print(f"Found {len(results)} books from Google Books")
    
    for book in results[:2]:
        print(f"Title: {book['title']}")
        print(f"Authors: {book['authors']}")
        print(f"ISBN-13: {book['isbn13']}")
        print(f"Rating: {book['average_rating']}")
        print("---")
