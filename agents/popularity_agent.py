"""
Popularity Analyzer Agent
Analyzes book popularity, ratings, and trending patterns
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
from .base_agent import BaseAgent, AgentMessage

logger = logging.getLogger(__name__)

class PopularityAnalyzerAgent(BaseAgent):
    """Agent responsible for analyzing book popularity and trends"""
    
    def __init__(self, agent_id: str = "popularity_001"):
        super().__init__(agent_id, "Popularity Analyzer Agent")
        self.capabilities = [
            "popularity_analysis",
            "trend_detection",
            "rating_analysis",
            "recommendation_scoring",
            "market_analysis"
        ]
        
        # Popularity metrics weights
        self.popularity_weights = {
            "average_rating": 0.3,
            "ratings_count": 0.25,
            "recent_trend": 0.2,
            "category_popularity": 0.15,
            "author_popularity": 0.1
        }
        
        logger.info(f"Popularity Analyzer Agent initialized with capabilities: {self.capabilities}")
    
    def get_capabilities(self) -> List[str]:
        return self.capabilities
    
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process popularity analysis requests"""
        try:
            if message.message_type == "analyze_popularity":
                return self._handle_popularity_analysis(message)
            elif message.message_type == "detect_trends":
                return self._handle_trend_detection(message)
            elif message.message_type == "score_recommendations":
                return self._handle_recommendation_scoring(message)
            elif message.message_type == "get_popular_books":
                return self._handle_popular_books_request(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    def _handle_popularity_analysis(self, message: AgentMessage) -> AgentMessage:
        """Analyze popularity of specific books"""
        books_data = message.content.get("books_data", [])
        analysis_type = message.content.get("analysis_type", "comprehensive")
        
        results = []
        for book in books_data:
            popularity_score = self._calculate_popularity_score(book)
            trend_score = self._calculate_trend_score(book)
            
            results.append({
                "isbn13": book.get("isbn13"),
                "title": book.get("title"),
                "popularity_score": popularity_score,
                "trend_score": trend_score,
                "overall_score": (popularity_score + trend_score) / 2,
                "analysis_timestamp": datetime.now().isoformat()
            })
        
        response_content = {
            "analysis_type": analysis_type,
            "books_analyzed": len(results),
            "results": results,
            "processing_time": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "popularity_analysis_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_trend_detection(self, message: AgentMessage) -> AgentMessage:
        """Detect trending books and categories"""
        books_df = pd.DataFrame(message.content.get("books_data", []))
        
        if books_df.empty:
            return self._create_error_response(message, "No books data provided")
        
        # Analyze trends by category
        category_trends = self._analyze_category_trends(books_df)
        
        # Analyze author trends
        author_trends = self._analyze_author_trends(books_df)
        
        # Identify trending books
        trending_books = self._identify_trending_books(books_df)
        
        response_content = {
            "category_trends": category_trends,
            "author_trends": author_trends,
            "trending_books": trending_books,
            "trend_analysis_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "trend_analysis_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_recommendation_scoring(self, message: AgentMessage) -> AgentMessage:
        """Score recommendations based on popularity"""
        recommendations = message.content.get("recommendations", [])
        user_preferences = message.content.get("user_preferences", {})
        
        scored_recommendations = []
        for rec in recommendations:
            score = self._calculate_recommendation_score(rec, user_preferences)
            scored_recommendations.append({
                **rec,
                "popularity_score": score,
                "scoring_timestamp": datetime.now().isoformat()
            })
        
        # Sort by score
        scored_recommendations.sort(key=lambda x: x["popularity_score"], reverse=True)
        
        response_content = {
            "scored_recommendations": scored_recommendations,
            "total_recommendations": len(scored_recommendations),
            "scoring_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "recommendation_scoring_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_popular_books_request(self, message: AgentMessage) -> AgentMessage:
        """Get popular books by category or criteria"""
        books_df = pd.DataFrame(message.content.get("books_data", []))
        criteria = message.content.get("criteria", {})
        
        if books_df.empty:
            return self._create_error_response(message, "No books data provided")
        
        # Filter and score books
        filtered_books = self._filter_books_by_criteria(books_df, criteria)
        scored_books = self._score_books_for_popularity(filtered_books)
        
        # Sort by popularity score
        scored_books = scored_books.sort_values("popularity_score", ascending=False)
        
        # Return top N books
        top_n = criteria.get("top_n", 10)
        top_books = scored_books.head(top_n).to_dict("records")
        
        response_content = {
            "popular_books": top_books,
            "criteria_used": criteria,
            "total_books_analyzed": len(scored_books),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "popular_books_result",
            response_content,
            priority=message.priority
        )
    
    def _calculate_popularity_score(self, book: Dict[str, Any]) -> float:
        """Calculate comprehensive popularity score"""
        score = 0.0
        
        # Rating component
        avg_rating = book.get("average_rating", 0)
        if avg_rating > 0:
            score += self.popularity_weights["average_rating"] * (avg_rating / 5.0)
        
        # Ratings count component (normalized)
        ratings_count = book.get("ratings_count", 0)
        if ratings_count > 0:
            normalized_count = min(np.log10(ratings_count + 1) / 5, 1.0)
            score += self.popularity_weights["ratings_count"] * normalized_count
        
        # Category popularity (simplified)
        category = book.get("simple_categories", "Other")
        category_score = self._get_category_popularity_score(category)
        score += self.popularity_weights["category_popularity"] * category_score
        
        return min(score, 1.0)
    
    def _calculate_trend_score(self, book: Dict[str, Any]) -> float:
        """Calculate trend score based on recent activity"""
        # Simplified trend calculation
        # In a real system, this would use historical data
        ratings_count = book.get("ratings_count", 0)
        avg_rating = book.get("average_rating", 0)
        
        # Higher ratings with moderate count suggest trending
        if ratings_count > 100 and avg_rating > 4.0:
            return 0.8
        elif ratings_count > 50 and avg_rating > 3.5:
            return 0.6
        else:
            return 0.3
    
    def _analyze_category_trends(self, books_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends by category"""
        if "simple_categories" not in books_df.columns:
            return {}
        
        category_stats = books_df.groupby("simple_categories").agg({
            "average_rating": "mean",
            "ratings_count": "sum",
            "isbn13": "count"
        }).round(2)
        
        # Calculate trend scores
        category_stats["trend_score"] = (
            category_stats["average_rating"] * 0.4 + 
            np.log10(category_stats["ratings_count"] + 1) * 0.6
        )
        
        return category_stats.to_dict("index")
    
    def _analyze_author_trends(self, books_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze trends by author"""
        if "authors" not in books_df.columns:
            return {}
        
        author_stats = books_df.groupby("authors").agg({
            "average_rating": "mean",
            "ratings_count": "sum",
            "isbn13": "count"
        }).round(2)
        
        # Filter authors with multiple books or high ratings
        trending_authors = author_stats[
            (author_stats["isbn13"] > 1) | (author_stats["average_rating"] > 4.0)
        ].sort_values("average_rating", ascending=False)
        
        return trending_authors.head(10).to_dict("index")
    
    def _identify_trending_books(self, books_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify trending books"""
        if books_df.empty:
            return []
        
        # Calculate trend score for each book
        books_df["trend_score"] = books_df.apply(self._calculate_trend_score, axis=1)
        
        # Sort by trend score
        trending = books_df.nlargest(20, "trend_score")
        
        return trending[["isbn13", "title", "authors", "trend_score", "average_rating"]].to_dict("records")
    
    def _calculate_recommendation_score(self, recommendation: Dict[str, Any], 
                                      user_preferences: Dict[str, Any]) -> float:
        """Calculate score for a recommendation based on user preferences"""
        base_score = self._calculate_popularity_score(recommendation)
        
        # Adjust based on user preferences
        if user_preferences.get("preferred_category"):
            if recommendation.get("simple_categories") == user_preferences["preferred_category"]:
                base_score *= 1.2
        
        if user_preferences.get("min_rating"):
            if recommendation.get("average_rating", 0) >= user_preferences["min_rating"]:
                base_score *= 1.1
        
        return min(base_score, 1.0)
    
    def _filter_books_by_criteria(self, books_df: pd.DataFrame, criteria: Dict[str, Any]) -> pd.DataFrame:
        """Filter books based on criteria"""
        filtered_df = books_df.copy()
        
        if criteria.get("min_rating"):
            filtered_df = filtered_df[filtered_df["average_rating"] >= criteria["min_rating"]]
        
        if criteria.get("min_ratings_count"):
            filtered_df = filtered_df[filtered_df["ratings_count"] >= criteria["min_ratings_count"]]
        
        if criteria.get("category"):
            filtered_df = filtered_df[filtered_df["simple_categories"] == criteria["category"]]
        
        return filtered_df
    
    def _score_books_for_popularity(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """Score books for popularity"""
        scored_df = books_df.copy()
        scored_df["popularity_score"] = scored_df.apply(self._calculate_popularity_score, axis=1)
        return scored_df
    
    def _get_category_popularity_score(self, category: str) -> float:
        """Get popularity score for a category"""
        category_scores = {
            "Fiction": 0.8,
            "Nonfiction": 0.7,
            "Children's Fiction": 0.6,
            "Children's Nonfiction": 0.5,
            "Other": 0.3
        }
        return category_scores.get(category, 0.3)
    
    def _create_error_response(self, original_message: AgentMessage, error_msg: str) -> AgentMessage:
        """Create error response message"""
        return self.send_message(
            original_message.sender_id,
            "error_response",
            {
                "error": error_msg,
                "original_message_id": original_message.message_id,
                "timestamp": datetime.now().isoformat()
            },
            priority=3
        )
