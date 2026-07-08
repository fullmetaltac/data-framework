CREATE TABLE IF NOT EXISTS events
(
    id              BIGSERIAL PRIMARY KEY,

    device_id       VARCHAR(100) NOT NULL,

    event_time      TIMESTAMP NOT NULL,

    temperature     NUMERIC(5,2),

    humidity        NUMERIC(5,2),

    pressure        NUMERIC(7,2),

    status          VARCHAR(30),

    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_device
ON events(device_id);

CREATE INDEX IF NOT EXISTS idx_events_time
ON events(event_time);
