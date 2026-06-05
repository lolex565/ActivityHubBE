CREATE TABLE IF NOT EXISTS profile_posts (
    id BIGSERIAL PRIMARY KEY,

    author_id INT NOT NULL
        REFERENCES users(id)
        ON DELETE CASCADE,

    content VARCHAR(500) NOT NULL,

    created_at TIMESTAMP NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_profile_posts_author_id
ON profile_posts(author_id);