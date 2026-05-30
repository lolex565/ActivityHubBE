CREATE TABLE IF NOT EXISTS follows (
    follower_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followed_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (follower_id, followed_id),
    CONSTRAINT ck_follows_no_self_follow CHECK (follower_id <> followed_id)
);

CREATE INDEX IF NOT EXISTS idx_follows_follower_followed
ON follows(follower_id, followed_id);

CREATE INDEX IF NOT EXISTS idx_follows_followed_follower
ON follows(followed_id, follower_id);