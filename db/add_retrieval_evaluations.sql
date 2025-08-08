CREATE TABLE IF NOT EXISTS retrieval_evaluations (
    id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES query_cache(id) ON DELETE CASCADE,
    chunk_id INTEGER REFERENCES document_chunks(id) ON DELETE CASCADE,
    relevance_score INTEGER CHECK (relevance_score IN (0, 1)) NOT NULL,
    llm_score NUMERIC,
    explanation TEXT,
    retrieval_method VARCHAR(50),
    rank_position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_retrieval_evaluations_query ON retrieval_evaluations(query_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_evaluations_chunk ON retrieval_evaluations(chunk_id);
CREATE INDEX IF NOT EXISTS idx_retrieval_eval_query_rank ON retrieval_evaluations(query_id, rank_position); 