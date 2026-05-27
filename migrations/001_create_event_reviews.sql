CREATE TABLE IF NOT EXISTS event_reviews (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    author_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_event_reviews_event_author UNIQUE (event_id, author_id),
    CONSTRAINT ck_event_reviews_comment_length CHECK (
        comment IS NULL OR char_length(comment) <= 1000
    )
);

CREATE INDEX IF NOT EXISTS idx_event_reviews_event_id ON event_reviews(event_id);
CREATE INDEX IF NOT EXISTS idx_event_reviews_author_id ON event_reviews(author_id);