-- Add multiple rating types to user_feedback table
ALTER TABLE user_feedback 
ADD COLUMN IF NOT EXISTS accuracy_rating INTEGER CHECK (accuracy_rating BETWEEN 1 AND 5),
ADD COLUMN IF NOT EXISTS comprehensiveness_rating INTEGER CHECK (comprehensiveness_rating BETWEEN 1 AND 5),
ADD COLUMN IF NOT EXISTS helpfulness_rating INTEGER CHECK (helpfulness_rating BETWEEN 1 AND 5);

-- Create indexes for the new rating columns for analytics
CREATE INDEX IF NOT EXISTS idx_user_feedback_accuracy_rating ON user_feedback(accuracy_rating) WHERE accuracy_rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_feedback_comprehensiveness_rating ON user_feedback(comprehensiveness_rating) WHERE comprehensiveness_rating IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_user_feedback_helpfulness_rating ON user_feedback(helpfulness_rating) WHERE helpfulness_rating IS NOT NULL;

-- Update the trigger to update the updated_at column when ratings change
CREATE OR REPLACE FUNCTION update_user_feedback_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_feedback_timestamp
    BEFORE UPDATE ON user_feedback
    FOR EACH ROW
    EXECUTE FUNCTION update_user_feedback_timestamp();