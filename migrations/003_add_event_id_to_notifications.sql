ALTER TABLE notifications
ADD COLUMN IF NOT EXISTS event_id INT REFERENCES events(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_notifications_event_id ON notifications(event_id);