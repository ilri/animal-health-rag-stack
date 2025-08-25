import json
from typing import List, Dict, Any
from models import FeedbackRequest
from utils import get_db_connection

class FeedbackService:
    def save_feedback(self, feedback: FeedbackRequest) -> Dict[str, Any]:
        """Save user feedback for a query."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if memory ID exists
                cursor.execute("SELECT id FROM query_cache WHERE id = %s", (feedback.memory_id,))
                if not cursor.fetchone():
                    return {
                        "status": "error",
                        "message": f"Memory entry with ID {feedback.memory_id} not found"
                    }
                
                # Check if feedback already exists
                cursor.execute("SELECT id FROM user_feedback WHERE query_cache_id = %s", (feedback.memory_id,))
                existing_feedback = cursor.fetchone()
                
                if existing_feedback:
                    # Update existing feedback
                    update_parts = []
                    update_values = []
                    
                    if feedback.feedback_text is not None:
                        update_parts.append("feedback_text = %s")
                        update_values.append(feedback.feedback_text)
                        
                    if feedback.rating is not None:
                        update_parts.append("rating = %s")
                        update_values.append(feedback.rating)
                    
                    if feedback.accuracy_rating is not None:
                        update_parts.append("accuracy_rating = %s")
                        update_values.append(feedback.accuracy_rating)
                    
                    if feedback.comprehensiveness_rating is not None:
                        update_parts.append("comprehensiveness_rating = %s")
                        update_values.append(feedback.comprehensiveness_rating)
                    
                    if feedback.helpfulness_rating is not None:
                        update_parts.append("helpfulness_rating = %s")
                        update_values.append(feedback.helpfulness_rating)
                        
                    if feedback.is_favorite is not None:
                        update_parts.append("is_favorite = %s")
                        update_values.append(feedback.is_favorite)
                    
                    update_parts.append("updated_at = CURRENT_TIMESTAMP")
                    
                    if update_parts:
                        query = f"""
                            UPDATE user_feedback 
                            SET {", ".join(update_parts)}
                            WHERE id = %s
                            RETURNING id
                        """
                        update_values.append(existing_feedback['id'])
                        cursor.execute(query, update_values)
                        updated_id = cursor.fetchone()['id']
                        conn.commit()
                        
                        return {
                            "status": "success",
                            "message": "Feedback updated successfully",
                            "id": updated_id
                        }
                else:
                    # Create new feedback
                    cursor.execute("""
                        INSERT INTO user_feedback 
                        (query_cache_id, feedback_text, rating, accuracy_rating, comprehensiveness_rating, helpfulness_rating, is_favorite)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        feedback.memory_id,
                        feedback.feedback_text,
                        feedback.rating,
                        feedback.accuracy_rating,
                        feedback.comprehensiveness_rating,
                        feedback.helpfulness_rating,
                        feedback.is_favorite if feedback.is_favorite is not None else False
                    ))
                    
                    new_id = cursor.fetchone()['id']
                    conn.commit()
                    
                    return {
                        "status": "success",
                        "message": "Feedback saved successfully",
                        "id": new_id
                    }
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorite queries."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        qc.id,
                        qc.query_text,
                        qc.answer_text,
                        qc.references,
                        qc.created_at,
                        uf.rating,
                        uf.accuracy_rating,
                        uf.comprehensiveness_rating,
                        uf.helpfulness_rating,
                        uf.feedback_text,
                        uf.created_at as favorited_at
                    FROM query_cache qc
                    INNER JOIN user_feedback uf ON qc.id = uf.query_cache_id
                    WHERE uf.is_favorite = true
                    ORDER BY uf.created_at DESC
                """)
                
                favorites = cursor.fetchall()
                
                return [
                    {
                        "id": fav["id"],
                        "query_cache_id": fav["id"],
                        "query_text": fav["query_text"],
                        "answer_text": fav["answer_text"],
                        "references": fav["references"] if isinstance(fav["references"], list) else (json.loads(fav["references"]) if fav["references"] else []),
                        "created_at": fav["created_at"].isoformat() if fav["created_at"] else None,
                        "rating": fav["rating"],
                        "accuracy_rating": fav["accuracy_rating"],
                        "comprehensiveness_rating": fav["comprehensiveness_rating"],
                        "helpfulness_rating": fav["helpfulness_rating"],
                        "feedback_text": fav["feedback_text"],
                        "favorited_at": fav["favorited_at"].isoformat() if fav["favorited_at"] else None
                    }
                    for fav in favorites
                ]
    
    def delete_feedback(self, memory_id: int) -> Dict[str, Any]:
        """Delete user feedback for a query."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Check if feedback exists
                cursor.execute("SELECT id FROM user_feedback WHERE query_cache_id = %s", (memory_id,))
                existing_feedback = cursor.fetchone()
                
                if not existing_feedback:
                    return {
                        "status": "error",
                        "message": f"No feedback found for memory ID {memory_id}"
                    }
                
                # Delete the feedback
                cursor.execute("DELETE FROM user_feedback WHERE query_cache_id = %s", (memory_id,))
                conn.commit()
                
                return {
                    "status": "success",
                    "message": "Feedback deleted successfully"
                }
    
    def get_feedback(self, memory_id: int) -> Dict[str, Any]:
        """Get feedback for a specific query."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT rating, accuracy_rating, comprehensiveness_rating, helpfulness_rating, feedback_text, is_favorite, created_at, updated_at
                    FROM user_feedback 
                    WHERE query_cache_id = %s
                """, (memory_id,))
                
                feedback = cursor.fetchone()
                
                if not feedback:
                    return {
                        "status": "error",
                        "message": f"No feedback found for memory ID {memory_id}"
                    }
                
                return {
                    "status": "success",
                    "feedback": {
                        "rating": feedback["rating"],
                        "accuracy_rating": feedback["accuracy_rating"],
                        "comprehensiveness_rating": feedback["comprehensiveness_rating"],
                        "helpfulness_rating": feedback["helpfulness_rating"],
                        "feedback_text": feedback["feedback_text"],
                        "is_favorite": feedback["is_favorite"],
                        "created_at": feedback["created_at"].isoformat() if feedback["created_at"] else None,
                        "updated_at": feedback["updated_at"].isoformat() if feedback["updated_at"] else None
                    }
                }