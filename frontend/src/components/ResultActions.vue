<template>
  <div class="result-actions">
    <div class="actions-bar">
      <div class="action-buttons">
        <button 
          class="action-btn favorite-btn" 
          :class="{ 'active': isFavorite }"
          @click="toggleFavorite"
          :title="isFavorite ? 'Remove from favorites' : 'Add to favorites'"
        >
          <span class="icon">
            <FontAwesomeIcon :icon="farStar" v-if="!isFavorite" />
            <FontAwesomeIcon :icon="faStar" v-if="isFavorite" />
          </span>
        </button>
        
        <button 
          class="action-btn thread-btn" 
          @click="createThread"
          :disabled="hasThread || !memoryId"
          :title="getThreadButtonTitle()"
        >
          <span class="icon">
            <FontAwesomeIcon :icon="faComments" />
          </span>
        </button>
        
        <button 
          class="action-btn feedback-btn" 
          @click="showFeedback = !showFeedback"
          :class="{ 'active': showFeedback }"
          title="Provide feedback"
        >
          <span class="icon">
            <FontAwesomeIcon :icon="faCommentDots" />
          </span>
        </button>
      </div>
      
      <div class="memory-indicator" v-if="fromMemory">
        <span class="from-memory-badge" title="Answer retrieved from memory">
          <FontAwesomeIcon :icon="faMemory" /> From memory
        </span>
      </div>
    </div>
    
    <div class="feedback-container" v-if="showFeedback">
      <div class="feedback-form">
        <h3>{{ existingFeedback ? 'Update Feedback' : 'Provide Feedback' }}</h3>
        
        <div class="rating-container">
          <div class="rating-label-row">
            <label>Rating:</label>
            <button 
              v-if="existingFeedback && existingFeedback.rating"
              class="clear-rating-btn"
              @click="clearRating"
              title="Clear rating"
            >
              <FontAwesomeIcon :icon="faTimes" />
            </button>
          </div>
          <div class="stars">
            <span 
              v-for="i in 5" 
              :key="i"
              @click="rating = i"
              :class="{ 'active': rating >= i }"
              class="star"
            >
              <FontAwesomeIcon :icon="faStar" />
            </span>
          </div>
        </div>
        
        <div class="feedback-text">
          <div class="feedback-label-row">
            <label for="feedback">Comment (optional):</label>
            <button 
              v-if="existingFeedback && existingFeedback.feedback_text"
              class="clear-comment-btn"
              @click="clearComment"
              title="Clear comment"
            >
              <FontAwesomeIcon :icon="faTimes" />
            </button>
          </div>
          <textarea 
            id="feedback" 
            v-model="feedbackText"
            placeholder="What did you think of this answer?"
            rows="3"
          ></textarea>
        </div>
        
        <div class="feedback-actions">
          <button 
            class="cancel-btn"
            @click="showFeedback = false"
          >
            Cancel
          </button>
          <button 
            v-if="existingFeedback"
            class="clear-all-btn"
            @click="clearAllFeedback"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Clearing...' : 'Clear All' }}
          </button>
          <button 
            class="submit-btn"
            @click="submitFeedback"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? 'Submitting...' : (existingFeedback ? 'Update Feedback' : 'Submit Feedback') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
  import { faStar, faComments, faCommentDots, faMemory, faTimes } from '@fortawesome/free-solid-svg-icons'
  import { faStar as farStar, faCalendarDays } from '@fortawesome/free-regular-svg-icons'
</script>

<script>
export default {
  name: 'ResultActions',
  props: {
    memoryId: {
      type: Number,
      required: false,
      default: null
    },
    fromMemory: {
      type: Boolean,
      default: false
    },
    initialFavorite: {
      type: Boolean,
      default: false
    },
    hasThread: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      showFeedback: false,
      rating: 0,
      feedbackText: '',
      isFavorite: this.initialFavorite,
      isSubmitting: false,
      existingFeedback: null
    }
  },
  methods: {
    async toggleFavorite() {
      try {
        this.isSubmitting = true;
        // Save to API
        const response = await fetch('/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            memory_id: this.memoryId,
            is_favorite: !this.isFavorite
          })
        });
        
        if (response.ok) {
          this.isFavorite = !this.isFavorite;
          this.$emit('favorite-changed', this.isFavorite);
        } else {
          console.error('Failed to update favorite status');
        }
      } catch (error) {
        console.error('Error updating favorite:', error);
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async submitFeedback() {
      if (this.rating === 0 && !this.feedbackText.trim() && !this.isFavorite) {
        alert('Please provide at least a rating, comment, or mark as favorite');
        return;
      }
      
      try {
        this.isSubmitting = true;
        
        // Submit feedback to API
        const response = await fetch('/api/feedback', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            memory_id: this.memoryId,
            rating: this.rating > 0 ? this.rating : null,
            feedback_text: this.feedbackText.trim() || null,
            is_favorite: this.isFavorite
          })
        });
        
        if (response.ok) {
          this.showFeedback = false;
          // Update existing feedback after successful submission
          await this.loadExistingFeedback();
          this.$emit('feedback-submitted');
        } else {
          console.error('Failed to submit feedback');
          alert('Failed to submit feedback. Please try again.');
        }
      } catch (error) {
        console.error('Error submitting feedback:', error);
        alert('Failed to submit feedback. Please try again.');
      } finally {
        this.isSubmitting = false;
      }
    },
    
    async loadExistingFeedback() {
      if (!this.memoryId) return;
      
      try {
        const response = await fetch(`/api/feedback/${this.memoryId}`);
        if (response.ok) {
          const data = await response.json();
          if (data.status === 'success') {
            this.existingFeedback = data.feedback;
            this.rating = data.feedback.rating || 0;
            this.feedbackText = data.feedback.feedback_text || '';
          }
        }
      } catch (error) {
        console.error('Error loading existing feedback:', error);
      }
    },
    
    clearRating() {
      this.rating = 0;
    },
    
    clearComment() {
      this.feedbackText = '';
    },
    
    async clearAllFeedback() {
      if (!confirm('Are you sure you want to remove all feedback for this answer?')) {
        return;
      }
      
      try {
        this.isSubmitting = true;
        
        const response = await fetch(`/api/feedback/${this.memoryId}`, {
          method: 'DELETE'
        });
        
        if (response.ok) {
          this.existingFeedback = null;
          this.rating = 0;
          this.feedbackText = '';
          this.isFavorite = false;
          this.showFeedback = false;
          this.$emit('feedback-cleared');
        } else {
          console.error('Failed to clear feedback');
          alert('Failed to clear feedback. Please try again.');
        }
      } catch (error) {
        console.error('Error clearing feedback:', error);
        alert('Failed to clear feedback. Please try again.');
      } finally {
        this.isSubmitting = false;
      }
    },
    
    createThread() {
      // Only emit the event if we have a valid memory ID
      if (this.memoryId) {
        this.$emit('create-thread');
      }
    },
    
    getThreadButtonTitle() {
      if (this.hasThread) {
        return 'Thread already exists';
      } else if (!this.memoryId) {
        return 'Cannot create thread without a valid memory ID';
      } else {
        return 'Create conversation thread';
      }
    }
  },
  watch: {
    showFeedback(newValue) {
      if (newValue && this.memoryId) {
        this.loadExistingFeedback();
      }
    }
  },
  mounted() {
    // Load existing feedback if memoryId is available
    if (this.memoryId) {
      this.loadExistingFeedback();
    }
  }
}
</script>

<style scoped>
.result-actions {
  margin-top: 1rem;
  border-top: 1px solid #eaeaea;
  padding-top: 0.75rem;
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.action-btn {
  background-color: #f5f5f5;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  padding: 0.5rem 0.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background-color: #e8e8e8;
}

.action-btn.active {
  background-color: #e0f2ff;
  border-color: #60b0ff;
  color: #0066cc;
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.favorite-btn.active {
  background-color: #fff8e0;
  border-color: #ffca28;
  color: #ff9800;
}

.memory-indicator {
  display: flex;
  align-items: center;
}

.from-memory-badge {
  background-color: #e0f7fa;
  color: #00838f;
  border-radius: 20px;
  padding: 0.25rem 0.75rem;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.feedback-container {
  margin-top: 1rem;
  padding: 1rem;
  background-color: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.feedback-form h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.rating-container {
  margin-bottom: 1rem;
}

.rating-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.rating-label-row label {
  margin: 0;
}

.stars {
  display: flex;
  gap: 0.25rem;
}

.star {
  cursor: pointer;
  color: #d1d1d1;
  font-size: 1.5rem;
  transition: color 0.2s ease;
}

.star:hover,
.star.active {
  color: #ffca28;
}

.feedback-text {
  margin-bottom: 1rem;
}

.feedback-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.feedback-label-row label {
  margin: 0;
}

.feedback-text textarea {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #ced4da;
  resize: vertical;
  font-family: inherit;
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

.cancel-btn,
.submit-btn,
.clear-all-btn {
  padding: 0.5rem 1rem;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: background-color 0.2s ease;
}

.cancel-btn {
  background-color: #e9ecef;
  color: #495057;
}

.cancel-btn:hover {
  background-color: #dee2e6;
}

.clear-rating-btn,
.clear-comment-btn {
  background: none;
  border: none;
  color: #dc3545;
  font-size: 0.9rem;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 3px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-rating-btn:hover,
.clear-comment-btn:hover {
  background-color: #f8d7da;
  color: #721c24;
}

.clear-all-btn {
  background-color: #f8d7da;
  color: #721c24;
}

.clear-all-btn:hover {
  background-color: #f1b0b7;
}

.clear-all-btn:disabled {
  background-color: #f8d7da;
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn {
  background-color: #0066cc;
  color: white;
}

.submit-btn:hover {
  background-color: #0055b3;
}

.submit-btn:disabled {
  background-color: #a0c4e4;
  cursor: not-allowed;
}
</style>
