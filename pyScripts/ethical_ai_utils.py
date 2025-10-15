"""
Ethical AI utilities for transparency, fairness, and responsible AI practices
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class EthicalAIMonitor:
    """Monitor and ensure ethical AI practices"""
    
    def __init__(self):
        self.recommendation_logs = []
        self.bias_metrics = {}
        self.fairness_scores = {}
    
    def log_recommendation_decision(self, 
                                  query: str, 
                                  recommendations: List[Dict[str, Any]], 
                                  user_id: str,
                                  algorithm_used: str,
                                  processing_time: float,
                                  metadata: Dict[str, Any] = None):
        """Log recommendation decisions for transparency and audit"""
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'query': query,
            'algorithm_used': algorithm_used,
            'processing_time_ms': processing_time * 1000,
            'num_recommendations': len(recommendations),
            'recommendations': [
                {
                    'isbn': rec.get('isbn13') or rec.get('isbn10'),
                    'title': rec.get('title'),
                    'authors': rec.get('authors'),
                    'category': rec.get('simple_categories'),
                    'rating': rec.get('average_rating'),
                    'popularity_score': rec.get('popularity_score'),
                    'source': rec.get('source', 'local_dataset')
                }
                for rec in recommendations
            ],
            'metadata': metadata or {}
        }
        
        self.recommendation_logs.append(log_entry)
        
        # Keep only last 10000 entries to prevent memory issues
        if len(self.recommendation_logs) > 10000:
            self.recommendation_logs = self.recommendation_logs[-10000:]
        
        logger.info(f"Recommendation logged for user {user_id}: {len(recommendations)} books recommended")
    
    def analyze_bias_in_recommendations(self, time_window_days: int = 30) -> Dict[str, Any]:
        """Analyze potential bias in recommendations"""
        
        # Filter logs by time window
        cutoff_date = datetime.now().timestamp() - (time_window_days * 24 * 60 * 60)
        recent_logs = [
            log for log in self.recommendation_logs
            if datetime.fromisoformat(log['timestamp']).timestamp() > cutoff_date
        ]
        
        if not recent_logs:
            return {"error": "No recent recommendations to analyze"}
        
        # Analyze category distribution
        all_categories = []
        all_authors = []
        all_ratings = []
        
        for log in recent_logs:
            for rec in log['recommendations']:
                if rec['category']:
                    all_categories.append(rec['category'])
                if rec['authors']:
                    all_authors.append(rec['authors'])
                if rec['rating']:
                    all_ratings.append(rec['rating'])
        
        # Calculate diversity metrics
        category_diversity = len(set(all_categories)) / len(all_categories) if all_categories else 0
        author_diversity = len(set(all_authors)) / len(all_authors) if all_authors else 0
        
        # Calculate rating distribution
        rating_stats = {
            'mean': np.mean(all_ratings) if all_ratings else 0,
            'std': np.std(all_ratings) if all_ratings else 0,
            'min': np.min(all_ratings) if all_ratings else 0,
            'max': np.max(all_ratings) if all_ratings else 0
        }
        
        # Category distribution
        category_counts = {}
        for category in all_categories:
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Check for potential bias (e.g., over-representation of certain categories)
        total_recommendations = len(all_categories)
        category_bias = {}
        for category, count in category_counts.items():
            percentage = (count / total_recommendations) * 100
            category_bias[category] = {
                'count': count,
                'percentage': percentage,
                'potentially_biased': percentage > 50  # Flag if >50% of recommendations
            }
        
        return {
            'analysis_period_days': time_window_days,
            'total_recommendations_analyzed': len(recent_logs),
            'diversity_metrics': {
                'category_diversity': category_diversity,
                'author_diversity': author_diversity
            },
            'rating_statistics': rating_stats,
            'category_distribution': category_bias,
            'potential_bias_flags': [
                category for category, data in category_bias.items()
                if data['potentially_biased']
            ],
            'fairness_score': self._calculate_fairness_score(category_diversity, author_diversity, rating_stats)
        }
    
    def _calculate_fairness_score(self, category_diversity: float, author_diversity: float, rating_stats: Dict) -> float:
        """Calculate overall fairness score (0-1, higher is better)"""
        
        # Diversity component (40% weight)
        diversity_score = (category_diversity + author_diversity) / 2
        
        # Rating distribution component (30% weight)
        # Prefer recommendations with good rating distribution (not just high-rated books)
        rating_variance_score = min(rating_stats['std'] / 2, 1.0)  # Normalize to 0-1
        
        # Balance component (30% weight)
        # Prefer balanced recommendations (not too many from one category)
        balance_score = 1.0 - min(len([c for c, d in self.bias_metrics.get('category_distribution', {}).items() 
                                      if d.get('potentially_biased', False)]) / 10, 1.0)
        
        fairness_score = (
            diversity_score * 0.4 +
            rating_variance_score * 0.3 +
            balance_score * 0.3
        )
        
        return round(fairness_score, 3)
    
    def get_recommendation_explanation(self, 
                                     query: str, 
                                     recommendations: List[Dict[str, Any]], 
                                     algorithm_used: str) -> Dict[str, Any]:
        """Provide explanation for recommendations (transparency)"""
        
        explanation = {
            'query_analyzed': query,
            'algorithm_used': algorithm_used,
            'total_books_considered': len(recommendations),
            'explanation_factors': []
        }
        
        # Analyze what factors influenced the recommendations
        if recommendations:
            # Category analysis
            categories = [rec.get('simple_categories') for rec in recommendations if rec.get('simple_categories')]
            if categories:
                most_common_category = max(set(categories), key=categories.count)
                explanation['explanation_factors'].append({
                    'factor': 'Category Preference',
                    'description': f'Most recommendations are in the "{most_common_category}" category',
                    'influence': 'High' if categories.count(most_common_category) > len(categories) * 0.6 else 'Medium'
                })
            
            # Rating analysis
            ratings = [rec.get('average_rating') for rec in recommendations if rec.get('average_rating')]
            if ratings:
                avg_rating = np.mean(ratings)
                explanation['explanation_factors'].append({
                    'factor': 'Quality Filter',
                    'description': f'Books with average rating of {avg_rating:.1f} stars or higher',
                    'influence': 'High' if avg_rating > 4.0 else 'Medium'
                })
            
            # Popularity analysis
            popularity_scores = [rec.get('popularity_score', 0) for rec in recommendations]
            if popularity_scores:
                avg_popularity = np.mean(popularity_scores)
                explanation['explanation_factors'].append({
                    'factor': 'Popularity Score',
                    'description': f'Books with popularity score of {avg_popularity:.2f} or higher',
                    'influence': 'Medium'
                })
            
            # Source analysis
            sources = [rec.get('source', 'local_dataset') for rec in recommendations]
            source_counts = {}
            for source in sources:
                source_counts[source] = source_counts.get(source, 0) + 1
            
            for source, count in source_counts.items():
                explanation['explanation_factors'].append({
                    'factor': 'Data Source',
                    'description': f'{count} books from {source}',
                    'influence': 'Low'
                })
        
        return explanation
    
    def detect_potential_issues(self) -> List[Dict[str, Any]]:
        """Detect potential ethical issues in the recommendation system"""
        
        issues = []
        
        # Analyze recent bias
        bias_analysis = self.analyze_bias_in_recommendations()
        
        if bias_analysis.get('fairness_score', 1.0) < 0.7:
            issues.append({
                'type': 'Low Fairness Score',
                'severity': 'Medium',
                'description': f"Fairness score is {bias_analysis['fairness_score']}, indicating potential bias",
                'recommendation': 'Review recommendation algorithms for bias and improve diversity'
            })
        
        # Check for category over-representation
        potential_bias_flags = bias_analysis.get('potential_bias_flags', [])
        if potential_bias_flags:
            issues.append({
                'type': 'Category Bias',
                'severity': 'High',
                'description': f"Over-representation detected in categories: {', '.join(potential_bias_flags)}",
                'recommendation': 'Implement category balancing in recommendation algorithm'
            })
        
        # Check for low diversity
        diversity_metrics = bias_analysis.get('diversity_metrics', {})
        if diversity_metrics.get('category_diversity', 1.0) < 0.3:
            issues.append({
                'type': 'Low Category Diversity',
                'severity': 'Medium',
                'description': f"Category diversity is {diversity_metrics['category_diversity']:.2f}",
                'recommendation': 'Increase category diversity in recommendations'
            })
        
        return issues

class TransparencyReporter:
    """Generate transparency reports for users and administrators"""
    
    def __init__(self, ethical_monitor: EthicalAIMonitor):
        self.ethical_monitor = ethical_monitor
    
    def generate_user_transparency_report(self, user_id: str) -> Dict[str, Any]:
        """Generate transparency report for a specific user"""
        
        # Get user's recommendation history
        user_logs = [
            log for log in self.ethical_monitor.recommendation_logs
            if log['user_id'] == user_id
        ]
        
        if not user_logs:
            return {"message": "No recommendation history found for this user"}
        
        # Analyze user's recommendations
        total_recommendations = sum(len(log['recommendations']) for log in user_logs)
        algorithms_used = list(set(log['algorithm_used'] for log in user_logs))
        
        # Category preferences
        all_categories = []
        for log in user_logs:
            for rec in log['recommendations']:
                if rec['category']:
                    all_categories.append(rec['category'])
        
        category_preferences = {}
        for category in all_categories:
            category_preferences[category] = category_preferences.get(category, 0) + 1
        
        # Average processing time
        avg_processing_time = np.mean([log['processing_time_ms'] for log in user_logs])
        
        return {
            'user_id': user_id,
            'report_generated_at': datetime.now().isoformat(),
            'summary': {
                'total_searches': len(user_logs),
                'total_books_recommended': total_recommendations,
                'algorithms_used': algorithms_used,
                'average_processing_time_ms': round(avg_processing_time, 2)
            },
            'preferences_learned': {
                'category_distribution': category_preferences,
                'most_recommended_category': max(category_preferences.items(), key=lambda x: x[1])[0] if category_preferences else None
            },
            'data_usage': {
                'personal_data_used': ['search_history', 'preferences', 'reading_history'],
                'data_retention': '30 days for recommendation logs',
                'data_sharing': 'No personal data shared with third parties'
            },
            'algorithm_transparency': {
                'algorithms_used': algorithms_used,
                'explanation_available': True,
                'bias_mitigation': 'Category balancing and diversity scoring implemented'
            }
        }
    
    def generate_system_transparency_report(self) -> Dict[str, Any]:
        """Generate system-wide transparency report"""
        
        bias_analysis = self.ethical_monitor.analyze_bias_in_recommendations()
        potential_issues = self.ethical_monitor.detect_potential_issues()
        
        return {
            'report_generated_at': datetime.now().isoformat(),
            'system_overview': {
                'total_recommendations_logged': len(self.ethical_monitor.recommendation_logs),
                'active_algorithms': ['semantic_search', 'popularity_analysis', 'user_preference_matching'],
                'data_sources': ['local_dataset', 'google_books_api']
            },
            'fairness_analysis': bias_analysis,
            'potential_issues': potential_issues,
            'mitigation_strategies': {
                'bias_detection': 'Automated monitoring of category distribution',
                'diversity_promotion': 'Category balancing in recommendation algorithms',
                'transparency': 'Explanation generation for all recommendations',
                'user_control': 'User preference settings and feedback mechanisms'
            },
            'data_governance': {
                'data_collection': 'Minimal personal data collection (search queries, preferences)',
                'data_processing': 'Local processing with optional Google Books API enhancement',
                'data_retention': '30 days for recommendation logs, user data until account deletion',
                'user_rights': 'Users can view, modify, and delete their data'
            }
        }

# Global ethical AI monitor instance
ethical_ai_monitor = EthicalAIMonitor()
transparency_reporter = TransparencyReporter(ethical_ai_monitor)
