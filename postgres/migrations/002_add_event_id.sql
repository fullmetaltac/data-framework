ALTER TABLE events
ADD COLUMN IF NOT EXISTS event_id UUID NOT NULL DEFAULT gen_random_uuid();

ALTER TABLE events
ALTER COLUMN event_id DROP DEFAULT;

CREATE UNIQUE INDEX IF NOT EXISTS idx_events_event_id
ON events(event_id);
