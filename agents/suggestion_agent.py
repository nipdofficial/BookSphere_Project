"""
Suggestion Agent
Main orchestrator that coordinates other agents to provide book recommendations
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .base_agent import BaseAgent, AgentMessage
from .classification_agent import ClassificationAgent
from .popularity_agent import PopularityAnalyzerAgent

logger = logging.getLogger(__name__)

class SuggestionAgent(BaseAgent):
    """Main agent that orchestrates book recommendations"""
    
    def __init__(self, agent_id: str = "suggestion_001"):
        super().__init__(agent_id, "Suggestion Agent")
        self.capabilities = [
            "semantic_search",
            "recommendation_orchestration",
            "user_preference_analysis",
            "multi_agent_coordination",
            "result_synthesis"
        ]
        
        # Initialize vector search components
        self.vector_db = None
        self.books_df = None
        
        # Agent references (will be set by communication hub)
        self.classification_agent = None
        self.popularity_agent = None
        
        logger.info(f"Suggestion Agent initialized with capabilities: {self.capabilities}")
    
    def get_capabilities(self) -> List[str]:
        return self.capabilities
    
    def set_agent_references(self, classification_agent: ClassificationAgent, 
                           popularity_agent: PopularityAnalyzerAgent):
        """Set references to other agents"""
        self.classification_agent = classification_agent
        self.popularity_agent = popularity_agent
        logger.info("Agent references set successfully")
    
    def set_data_sources(self, vector_db, books_df: pd.DataFrame):
        """Set data sources for recommendations"""
        self.vector_db = vector_db
        self.books_df = books_df
        logger.info(f"Data sources set: {len(books_df)} books loaded")
    
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process recommendation requests"""
        try:
            if message.message_type == "get_recommendations":
                return self._handle_recommendation_request(message)
            elif message.message_type == "semantic_search":
                return self._handle_semantic_search(message)
            elif message.message_type == "analyze_user_preferences":
                return self._handle_user_preference_analysis(message)
            elif message.message_type == "get_personalized_recommendations":
                return self._handle_personalized_recommendations(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    def _handle_recommendation_request(self, message: AgentMessage) -> AgentMessage:
        """Handle general recommendation requests"""
        query = message.content.get("query", "")
        filters = message.content.get("filters", {})
        top_k = message.content.get("top_k", 10)
        
        # Step 1: Semantic search
        semantic_results = self._perform_semantic_search(query, top_k * 2)
        
        # Step 2: Apply filters
        filtered_results = self._apply_filters(semantic_results, filters)
        
        # Step 3: Get popularity scores
        popularity_scores = self._get_popularity_scores(filtered_results)
        
        # Step 4: Synthesize final recommendations
        final_recommendations = self._synthesize_recommendations(
            filtered_results, popularity_scores, top_k
        )
        
        response_content = {
            "query": query,
            "filters_applied": filters,
            "recommendations": final_recommendations,
            "total_found": len(semantic_results),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "recommendation_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_semantic_search(self, message: AgentMessage) -> AgentMessage:
        """Handle semantic search requests"""
        query = message.content.get("query", "")
        top_k = message.content.get("top_k", 10)
        
        results = self._perform_semantic_search(query, top_k)
        
        response_content = {
            "query": query,
            "results": results,
            "total_results": len(results),
            "search_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "semantic_search_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_user_preference_analysis(self, message: AgentMessage) -> AgentMessage:
        """Analyze user preferences from query and history"""
        query = message.content.get("query", "")
        user_history = message.content.get("user_history", [])
        
        # Analyze query for preferences
        query_preferences = self._extract_preferences_from_query(query)
        
        # Analyze user history
        history_preferences = self._analyze_user_history(user_history)
        
        # Combine preferences
        combined_preferences = self._combine_preferences(query_preferences, history_preferences)
        
        response_content = {
            "query_preferences": query_preferences,
            "history_preferences": history_preferences,
            "combined_preferences": combined_preferences,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "preference_analysis_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_personalized_recommendations(self, message: AgentMessage) -> AgentMessage:
        """Handle personalized recommendation requests"""
        query = message.content.get("query", "")
        user_preferences = message.content.get("user_preferences", {})
        user_history = message.content.get("user_history", [])
        top_k = message.content.get("top_k", 10)
        
        # Step 1: Analyze user preferences
        preference_analysis = self._analyze_user_preferences(query, user_history)
        
        # Step 2: Semantic search with preferences
        semantic_results = self._perform_personalized_search(query, preference_analysis, top_k * 2)
        
        # Step 3: Apply user-specific filters
        personalized_results = self._apply_personalized_filters(semantic_results, user_preferences)
        
        # Step 4: Score and rank
        final_recommendations = self._score_personalized_recommendations(
            personalized_results, user_preferences, top_k
        )
        
        response_content = {
            "query": query,
            "user_preferences": user_preferences,
            "preference_analysis": preference_analysis,
            "recommendations": final_recommendations,
            "personalization_score": self._calculate_personalization_score(final_recommendations, user_preferences),
            "processing_timestamp": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "personalized_recommendation_result",
            response_content,
            priority=message.priority
        )
    
    def _perform_semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic search using vector database"""
        if not self.vector_db or not self.books_df is not None:
            logger.error("Vector database or books data not available")
            return []
        
        try:
            # Perform similarity search
            docs = self.vector_db.similarity_search(query, k=top_k)
            
            # Extract ISBNs and get book data
            results = []
            for doc in docs:
                try:
                    # Extract ISBN from document content
                    isbn_str = doc.page_content.strip().split()[0]
                    isbn_num = int(''.join(filter(str.isdigit, isbn_str)))
                    
                    # Get book data
                    book_data = self.books_df[self.books_df["isbn13"] == isbn_num]
                    if not book_data.empty:
                        book_info = book_data.iloc[0].to_dict()
                        results.append(book_info)
                        
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error extracting ISBN from document: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def _apply_filters(self, results: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to search results"""
        filtered_results = results.copy()
        
        # Category filter
        if filters.get("category") and filters["category"] != "All":
            filtered_results = [r for r in filtered_results 
                              if r.get("simple_categories") == filters["category"]]
        
        # Rating filter
        if filters.get("min_rating"):
            filtered_results = [r for r in filtered_results 
                              if r.get("average_rating", 0) >= filters["min_rating"]]
        
        # Emotion filter
        if filters.get("emotion_tone") and filters["emotion_tone"] != "All":
            emotion_scores = self._get_emotion_scores(filtered_results)
            filtered_results = self._filter_by_emotion(filtered_results, emotion_scores, filters["emotion_tone"])
        
        return filtered_results
    
    def _get_popularity_scores(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Get popularity scores for results"""
        if not self.popularity_agent:
            return {}
        
        # Create message for popularity agent
        message_content = {
            "books_data": results,
            "analysis_type": "recommendation_scoring"
        }
        
        # This would normally be sent through the communication hub
        # For now, we'll calculate scores directly
        scores = {}
        for book in results:
            score = self._calculate_simple_popularity_score(book)
            scores[book.get("isbn13", "")] = score
        
        return scores
    
    def _synthesize_recommendations(self, results: List[Dict[str, Any]], 
                                  popularity_scores: Dict[str, float], 
                                  top_k: int) -> List[Dict[str, Any]]:
        """Synthesize final recommendations"""
        # Remove duplicates based on ISBN
        seen_isbns = set()
        unique_results = []
        
        for result in results:
            isbn = result.get("isbn13", "")
            if isbn and isbn not in seen_isbns:
                seen_isbns.add(isbn)
                unique_results.append(result)
        
        # Add popularity scores to results
        for result in unique_results:
            isbn = result.get("isbn13", "")
            result["popularity_score"] = popularity_scores.get(isbn, 0.0)
        
        # Sort by popularity score
        sorted_results = sorted(unique_results, key=lambda x: x.get("popularity_score", 0), reverse=True)
        
        # Return top_k results
        return sorted_results[:top_k]
    
    def _extract_preferences_from_query(self, query: str) -> Dict[str, Any]:
        """Extract user preferences from query text"""
        preferences = {
            "preferred_genres": [],
            "emotion_preference": None,
            "complexity_level": "medium"
        }
        
        query_lower = query.lower()
        
        # Genre detection
        if any(word in query_lower for word in ["fiction", "novel", "story"]):
            preferences["preferred_genres"].append("Fiction")
        if any(word in query_lower for word in ["nonfiction", "biography", "history"]):
            preferences["preferred_genres"].append("Nonfiction")
        if any(word in query_lower for word in ["children", "kids", "young"]):
            preferences["preferred_genres"].append("Children's Fiction")
        
        # Emotion detection
        if any(word in query_lower for word in ["happy", "joyful", "uplifting"]):
            preferences["emotion_preference"] = "joy"
        elif any(word in query_lower for word in ["sad", "emotional", "touching"]):
            preferences["emotion_preference"] = "sadness"
        elif any(word in query_lower for word in ["exciting", "thrilling", "adventure"]):
            preferences["emotion_preference"] = "surprise"
        
        return preferences
    
    def _analyze_user_history(self, user_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user's reading history"""
        if not user_history:
            return {}
        
        # Calculate preferences from history
        categories = [book.get("simple_categories") for book in user_history if book.get("simple_categories")]
        avg_rating = np.mean([book.get("average_rating", 0) for book in user_history if book.get("average_rating")])
        
        return {
            "preferred_categories": list(set(categories)),
            "average_rating_preference": avg_rating,
            "total_books_read": len(user_history)
        }
    
    def _combine_preferences(self, query_prefs: Dict[str, Any], 
                           history_prefs: Dict[str, Any]) -> Dict[str, Any]:
        """Combine query and history preferences"""
        combined = {
            "preferred_genres": [],
            "emotion_preference": query_prefs.get("emotion_preference"),
            "min_rating": history_prefs.get("average_rating_preference", 3.0),
            "preferred_categories": history_prefs.get("preferred_categories", [])
        }
        
        # Combine genres
        combined["preferred_genres"] = list(set(
            query_prefs.get("preferred_genres", []) + 
            history_prefs.get("preferred_categories", [])
        ))
        
        return combined
    
    def _perform_personalized_search(self, query: str, preferences: Dict[str, Any], top_k: int) -> List[Dict[str, Any]]:
        """Perform personalized semantic search"""
        # Start with semantic search
        results = self._perform_semantic_search(query, top_k)
        
        # Boost results that match preferences
        for result in results:
            boost_score = 0.0
            
            # Category boost
            if result.get("simple_categories") in preferences.get("preferred_genres", []):
                boost_score += 0.2
            
            # Rating boost
            if result.get("average_rating", 0) >= preferences.get("min_rating", 3.0):
                boost_score += 0.1
            
            result["personalization_boost"] = boost_score
        
        # Sort by personalization boost
        results.sort(key=lambda x: x.get("personalization_boost", 0), reverse=True)
        
        return results
    
    def _apply_personalized_filters(self, results: List[Dict[str, Any]], 
                                 user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply personalized filters"""
        filtered_results = results.copy()
        
        # Apply minimum rating filter
        min_rating = user_preferences.get("min_rating", 3.0)
        filtered_results = [r for r in filtered_results 
                          if r.get("average_rating", 0) >= min_rating]
        
        return filtered_results
    
    def _score_personalized_recommendations(self, results: List[Dict[str, Any]], 
                                         user_preferences: Dict[str, Any], 
                                         top_k: int) -> List[Dict[str, Any]]:
        """Score and rank personalized recommendations"""
        # Remove duplicates based on ISBN
        seen_isbns = set()
        unique_results = []
        
        for result in results:
            isbn = result.get("isbn13", "")
            if isbn and isbn not in seen_isbns:
                seen_isbns.add(isbn)
                unique_results.append(result)
        
        # Calculate final scores
        for result in unique_results:
            base_score = result.get("popularity_score", 0.0)
            boost_score = result.get("personalization_boost", 0.0)
            result["final_score"] = base_score + boost_score
        
        # Sort by final score
        sorted_results = sorted(unique_results, key=lambda x: x.get("final_score", 0), reverse=True)
        
        return sorted_results[:top_k]
    
    def _calculate_personalization_score(self, recommendations: List[Dict[str, Any]], 
                                       user_preferences: Dict[str, Any]) -> float:
        """Calculate how well recommendations match user preferences"""
        if not recommendations:
            return 0.0
        
        total_score = 0.0
        for rec in recommendations:
            score = 0.0
            
            # Category match
            if rec.get("simple_categories") in user_preferences.get("preferred_genres", []):
                score += 0.5
            
            # Rating match
            if rec.get("average_rating", 0) >= user_preferences.get("min_rating", 3.0):
                score += 0.5
            
            total_score += score
        
        return total_score / len(recommendations)
    
    def _get_emotion_scores(self, results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
        """Get emotion scores for results"""
        emotion_scores = {}
        
        for result in results:
            isbn = result.get("isbn13", "")
            emotions = {
                "joy": result.get("joy", 0.0),
                "sadness": result.get("sadness", 0.0),
                "anger": result.get("anger", 0.0),
                "fear": result.get("fear", 0.0),
                "surprise": result.get("surprise", 0.0)
            }
            emotion_scores[isbn] = emotions
        
        return emotion_scores
    
    def _filter_by_emotion(self, results: List[Dict[str, Any]], 
                         emotion_scores: Dict[str, Dict[str, float]], 
                         emotion_tone: str) -> List[Dict[str, Any]]:
        """Filter results by emotion tone"""
        emotion_mapping = {
            "Happy": "joy",
            "Sad": "sadness", 
            "Angry": "anger",
            "Suspenseful": "fear",
            "Surprising": "surprise"
        }
        
        target_emotion = emotion_mapping.get(emotion_tone, "joy")
        
        # Sort by target emotion score
        for result in results:
            isbn = result.get("isbn13", "")
            result["emotion_score"] = emotion_scores.get(isbn, {}).get(target_emotion, 0.0)
        
        # Sort by emotion score
        sorted_results = sorted(results, key=lambda x: x.get("emotion_score", 0), reverse=True)
        
        return sorted_results
    
    def _calculate_simple_popularity_score(self, book: Dict[str, Any]) -> float:
        """Calculate simple popularity score"""
        rating = book.get("average_rating", 0)
        count = book.get("ratings_count", 0)
        
        # Normalize rating (0-1)
        rating_score = rating / 5.0
        
        # Normalize count (log scale)
        count_score = min(np.log10(count + 1) / 5, 1.0)
        
        # Combined score
        return (rating_score * 0.6) + (count_score * 0.4)
    
    def _analyze_user_preferences(self, query: str, user_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze user preferences from query and history"""
        query_prefs = self._extract_preferences_from_query(query)
        history_prefs = self._analyze_user_history(user_history)
        return self._combine_preferences(query_prefs, history_prefs)
    
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
