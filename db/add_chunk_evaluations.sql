CREATE TABLE IF NOT EXISTS chunk_evaluations (
    id SERIAL PRIMARY KEY,
    chunk_id INTEGER REFERENCES document_chunks(id) ON DELETE CASCADE,
    evaluation_criteria VARCHAR(100) NOT NULL,
    score INTEGER CHECK (score IN (0, 1)) NOT NULL,
    explanation TEXT,
    model_used VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunk_evaluations_chunk_id ON chunk_evaluations(chunk_id);
CREATE INDEX IF NOT EXISTS idx_chunk_evaluations_criteria ON chunk_evaluations(evaluation_criteria); 