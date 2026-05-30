CREATE TYPE user_role AS ENUM ('USER', 'ADMIN', 'ORGANIZER');
CREATE TYPE event_status AS ENUM ('DRAFT', 'ACTIVE', 'STARTED', 'CANCELLED', 'FINISHED');
CREATE TYPE event_user_status AS ENUM ('INTERESTED', 'PARTICIPANT');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash TEXT NOT NULL,
    birth_date DATE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    identity_confirmed BOOLEAN NOT NULL DEFAULT FALSE,
    role user_role NOT NULL DEFAULT 'USER',
    university VARCHAR(255),
    faculty VARCHAR(255),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_settings (
    user_id INT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    event_announcements BOOLEAN NOT NULL DEFAULT TRUE,
    calendar_reminders BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE follows (
    follower_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    followed_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (follower_id, followed_id),
    CONSTRAINT ck_follows_no_self_follow CHECK (follower_id <> followed_id)
);

CREATE INDEX idx_follows_follower_followed
ON follows(follower_id, followed_id);

CREATE INDEX idx_follows_followed_follower
ON follows(followed_id, follower_id);

CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    organizer_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(100),
    location_name VARCHAR(255),
    latitude DECIMAL(9,6) NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DECIMAL(9,6) NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    max_participants INT CHECK (max_participants > 0),
    status event_status NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_events (
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    status event_user_status NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, event_id)
);

CREATE TABLE event_reviews (
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

CREATE TABLE announcements (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    announcement_date DATE NOT NULL,
    announcement_time TIME NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    event_id INT NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    event_id INT REFERENCES events(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_events_event_id ON user_events(event_id);
CREATE INDEX idx_events_date_time ON events(event_date, event_time);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_type ON events(type);
CREATE INDEX idx_events_location_name ON events(location_name);
CREATE INDEX idx_events_name ON events(name);
CREATE INDEX idx_messages_event_id ON messages(event_id);
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_announcements_event_id ON announcements(event_id);
CREATE INDEX idx_event_reviews_event_id ON event_reviews(event_id);
CREATE INDEX idx_event_reviews_author_id ON event_reviews(author_id);