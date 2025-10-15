"""
Text Classification Agent
Handles book categorization and genre classification using NLP
"""

import pandas as pd
import numpy as np
from transformers import pipeline
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime
from .base_agent import BaseAgent, AgentMessage

logger = logging.getLogger(__name__)

class ClassificationAgent(BaseAgent):
    """Agent responsible for text classification and categorization"""
    
    def __init__(self, agent_id: str = "classifier_001"):
        super().__init__(agent_id, "Text Classification Agent")
        self.capabilities = [
            "text_classification",
            "genre_detection", 
            "category_mapping",
            "zero_shot_classification"
        ]
        
        # Initialize classification models
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            top_k=None,
            device=-1
        )
        
        self.zero_shot_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1
        )
        
        # Category mapping
        self.category_mapping = {
            'Fiction': "Fiction",
            'Juvenile Fiction': "Children's Fiction",
            'Biography & Autobiography': "Nonfiction",
            'History': "Nonfiction",
            'Literary Criticism': "Nonfiction",
            'Philosophy': "Nonfiction",
            'Religion': "Nonfiction",
            'Comics & Graphic Novels': "Fiction",
            'Drama': "Fiction",
            'Juvenile Nonfiction': "Children's Nonfiction",
            'Science': "Nonfiction",
            'Poetry': "Fiction"
        }
        
        logger.info(f"Classification Agent initialized with capabilities: {self.capabilities}")
    
    def get_capabilities(self) -> List[str]:
        return self.capabilities
    
    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """Process classification requests"""
        try:
            if message.message_type == "classify_text":
                return self._handle_text_classification(message)
            elif message.message_type == "detect_emotion":
                return self._handle_emotion_detection(message)
            elif message.message_type == "categorize_book":
                return self._handle_book_categorization(message)
            else:
                logger.warning(f"Unknown message type: {message.message_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return self._create_error_response(message, str(e))
    
    def _handle_text_classification(self, message: AgentMessage) -> AgentMessage:
        """Handle text classification requests"""
        text = message.content.get("text", "")
        categories = message.content.get("categories", ["Fiction", "Nonfiction"])
        
        # Perform zero-shot classification
        result = self.zero_shot_classifier(text, categories)
        
        response_content = {
            "original_text": text,
            "predicted_category": result["labels"][0],
            "confidence_scores": dict(zip(result["labels"], result["scores"])),
            "processing_time": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "classification_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_emotion_detection(self, message: AgentMessage) -> AgentMessage:
        """Handle emotion detection requests"""
        text = message.content.get("text", "")
        
        # Perform emotion classification
        emotions = self.emotion_classifier(text)
        
        # Extract emotion scores
        emotion_scores = {}
        for emotion in emotions[0]:
            emotion_scores[emotion["label"]] = emotion["score"]
        
        # Find dominant emotion
        dominant_emotion = max(emotion_scores.items(), key=lambda x: x[1])
        
        response_content = {
            "original_text": text,
            "dominant_emotion": dominant_emotion[0],
            "emotion_confidence": dominant_emotion[1],
            "all_emotions": emotion_scores,
            "processing_time": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "emotion_result",
            response_content,
            priority=message.priority
        )
    
    def _handle_book_categorization(self, message: AgentMessage) -> AgentMessage:
        """Handle book categorization requests"""
        book_data = message.content.get("book_data", {})
        description = book_data.get("description", "")
        existing_category = book_data.get("category", "")
        
        # If no existing category, classify using zero-shot
        if not existing_category:
            categories = list(self.category_mapping.keys())
            result = self.zero_shot_classifier(description, categories)
            predicted_category = result["labels"][0]
        else:
            predicted_category = existing_category
        
        # Map to simple category
        simple_category = self.category_mapping.get(predicted_category, "Other")
        
        response_content = {
            "book_isbn": book_data.get("isbn13", ""),
            "original_category": existing_category,
            "predicted_category": predicted_category,
            "simple_category": simple_category,
            "confidence": result["scores"][0] if not existing_category else 1.0,
            "processing_time": datetime.now().isoformat()
        }
        
        return self.send_message(
            message.sender_id,
            "categorization_result",
            response_content,
            priority=message.priority
        )
    
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
    
    def classify_batch_books(self, books_df: pd.DataFrame) -> pd.DataFrame:
        """Classify multiple books at once"""
        logger.info(f"Starting batch classification for {len(books_df)} books")
        
        results = []
        for idx, row in books_df.iterrows():
            try:
                description = str(row.get("description", ""))
                if description and description != "nan":
                    result = self.zero_shot_classifier(
                        description, 
                        list(self.category_mapping.keys())
                    )
                    predicted_category = result["labels"][0]
                    simple_category = self.category_mapping.get(predicted_category, "Other")
                    
                    results.append({
                        "isbn13": row.get("isbn13"),
                        "predicted_category": predicted_category,
                        "simple_category": simple_category,
                        "confidence": result["scores"][0]
                    })
            except Exception as e:
                logger.error(f"Error classifying book {row.get('isbn13', 'unknown')}: {e}")
                results.append({
                    "isbn13": row.get("isbn13"),
                    "predicted_category": "Unknown",
                    "simple_category": "Other",
                    "confidence": 0.0
                })
        
        return pd.DataFrame(results)
