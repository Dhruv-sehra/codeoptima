"""
Feedback system for CodeOptima
Tracks user feedback to improve suggestions
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any
import pandas as pd


class FeedbackSystem:
    """Handles user feedback for continuous improvement"""
    
    def __init__(self):
        self.feedback_file = "data/feedback/feedback.json"
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize feedback storage"""
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        
        if not os.path.exists(self.feedback_file):
            with open(self.feedback_file, 'w') as f:
                json.dump([], f)
    
    def record_feedback(self, 
                       issue_type: str,
                       suggestion: str,
                       user_feedback: str,  # 'helpful', 'not_helpful', 'suggest_improvement'
                       user_comment: str = "",
                       code_snippet: str = ""):
        """Record user feedback for a suggestion"""
        
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'issue_type': issue_type,
            'suggestion': suggestion,
            'user_feedback': user_feedback,
            'user_comment': user_comment,
            'code_snippet_hash': hash(code_snippet[:100]) if code_snippet else None
        }
        
        # Load existing feedback
        try:
            with open(self.feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except:
            feedback_data = []
        
        # Add new feedback
        feedback_data.append(feedback_entry)
        
        # Keep only last 1000 entries
        if len(feedback_data) > 1000:
            feedback_data = feedback_data[-1000:]
        
        # Save back
        with open(self.feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        return True
    
    def get_feedback_stats(self) -> Dict[str, Any]:
        """Get statistics from feedback data"""
        try:
            with open(self.feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except:
            return {'total_feedback': 0}
        
        if not feedback_data:
            return {'total_feedback': 0}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(feedback_data)
        
        stats = {
            'total_feedback': len(feedback_data),
            'helpful_count': len(df[df['user_feedback'] == 'helpful']),
            'not_helpful_count': len(df[df['user_feedback'] == 'not_helpful']),
            'suggestions_count': len(df[df['user_feedback'] == 'suggest_improvement']),
            'by_issue_type': df['issue_type'].value_counts().to_dict()
        }
        
        # Calculate helpful rate
        helpful = stats['helpful_count']
        not_helpful = stats['not_helpful_count']
        total_rated = helpful + not_helpful
        
        if total_rated > 0:
            stats['helpful_rate'] = helpful / total_rated
        else:
            stats['helpful_rate'] = 0
        
        return stats
    
    def get_improvement_suggestions(self) -> List[Dict[str, Any]]:
        """Get user suggestions for improvement"""
        try:
            with open(self.feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except:
            return []
        
        improvements = []
        for entry in feedback_data:
            if entry['user_feedback'] == 'suggest_improvement' and entry['user_comment']:
                improvements.append({
                    'comment': entry['user_comment'],
                    'issue_type': entry['issue_type'],
                    'timestamp': entry['timestamp']
                })
        
        return improvements[:10]  # Return top 10
    
    def adjust_suggestion_confidence(self, issue_type: str) -> float:
        """Adjust suggestion confidence based on feedback"""
        stats = self.get_feedback_stats()
        
        if stats['total_feedback'] == 0:
            return 0.7  # Default confidence
        
        # Get feedback for this issue type
        try:
            with open(self.feedback_file, 'r') as f:
                feedback_data = json.load(f)
        except:
            return 0.7
        
        type_feedback = [f for f in feedback_data if f['issue_type'] == issue_type]
        
        if not type_feedback:
            return 0.7
        
        helpful = len([f for f in type_feedback if f['user_feedback'] == 'helpful'])
        not_helpful = len([f for f in type_feedback if f['user_feedback'] == 'not_helpful'])
        total = helpful + not_helpful
        
        if total == 0:
            return 0.7
        
        # Adjust confidence based on helpful rate
        helpful_rate = helpful / total
        
        if helpful_rate > 0.8:
            return 0.9  # High confidence
        elif helpful_rate > 0.5:
            return 0.7  # Medium confidence
        else:
            return 0.5  # Low confidence, needs improvement


# Global feedback system
feedback_system = FeedbackSystem()