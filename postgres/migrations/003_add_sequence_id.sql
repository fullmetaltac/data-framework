ALTER TABLE events
ADD COLUMN IF NOT EXISTS sequence_id INTEGER NOT NULL DEFAULT 0;

ALTER TABLE events
ALTER COLUMN sequence_id DROP DEFAULT;

CREATE INDEX IF NOT EXISTS idx_events_device_sequence
ON events(device_id, sequence_id);
