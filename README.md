# Data Framework

A small data pipeline for generating and storing events:

```text
Generator -> Kafka -> Consumer -> PostgreSQL -> Schema checks
                          |                      Quality checks
                          v                      Business checks
                      events-dlq                 Reconciliation
                  (invalid messages)              Sequence report
```

The generator creates events and sends them to Kafka. The consumer receives the
messages, validates them using the Pydantic `Event` model, and stores them in the
`events` table through SQLAlchemy. A message that fails validation is never
silently dropped: it is published to the `events-dlq` topic instead, alongside
the validation error, a timestamp, and the source topic, so it can be inspected
or replayed later. See [End-to-End Reconciliation](#end-to-end-reconciliation),
[Dead-Letter Queue](#dead-letter-queue), and
[Out-of-Order and Missing Sequence Detection](#out-of-order-and-missing-sequence-detection)
below for how the pipeline verifies that no event is lost, corrupted, or
delivered out of order without being noticed.

## Requirements

- Python 3.11+
- Docker Desktop
- Docker Compose

Run all commands below from the project root.

## 1. Prepare Python

Create and activate a virtual environment in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install the dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the tests:

```powershell
python -m pytest -v
```

The generator unit tests do not require infrastructure:

```powershell
python -m pytest tests/unit -v
```

Schema, quality, and business tests query PostgreSQL and require the
infrastructure to be running. They verify the `events` table structure,
temperature completeness and range, `(device_id, event_time)` uniqueness,
five-minute freshness, device count, and allowed statuses.

## Declarative Data Quality API

Reusable checks live in `src.quality`; project tests only declare their rules:

```python
Check.range("temperature", -40, 80).run(db_connection)
Check.freshness("event_time", minutes=5).run(db_connection)
```

Several rules can be composed into a table specification:

```python
(
    Table("events")
    .not_null("device_id")
    .range("temperature", -40, 80)
    .unique("device_id", "event_time")
    .run(db_connection)
)
```

The column-focused expectation DSL is also available:

```python
expect(table="events").column("temperature").to_be_between(
    -40, 80, db_connection
)
```

If no connection is supplied, `run()` uses the configured `DATABASE_URL`.

## End-to-End Reconciliation

Data quality checks confirm that the rows in PostgreSQL are well-formed, but they
cannot tell you whether events were lost between Kafka and PostgreSQL. Every
`Event` carries a unique `event_id` (a UUID) precisely so that can be verified.

`src.quality.reconcile` reads every `event_id` published to the `events` Kafka
topic (the source of truth) and every `event_id` stored in the `events` table
(the target), then compares the two sets:

```powershell
python -m src.quality.reconcile
```

```text
Source events: 1000
Target events: 997

Missing:    3
Duplicates: 2
Unexpected: 1
```

- **Missing** — event IDs seen on Kafka but never stored (for example, events the
  consumer rejected for failing validation).
- **Duplicates** — event IDs published to Kafka more than once (the generator's
  `duplicate` defect resends the same `event_id`; the consumer relies on the
  `events.event_id` unique constraint to avoid storing it twice).
- **Unexpected** — event IDs present in PostgreSQL but never seen on Kafka,
  which should never happen and indicates a bug if it does.

The script exits with status `1` if anything is missing or unexpected. The
comparison logic itself (`src.quality.reconciliation.reconcile`) is pure and unit
tested in `tests/unit/test_reconciliation.py` without requiring any infrastructure.

## Dead-Letter Queue

A message that fails `Event` validation (a poison message) is published to the
`events-dlq` Kafka topic instead of being dropped:

```json
{
  "original_message": { "device_id": "", "temperature": null, "..." : "..." },
  "error": "1 validation error for Event\ntemperature\n  Input should be a valid number ...",
  "failed_at": "2026-08-22T19:36:20.595518+00:00",
  "source_topic": "events"
}
```

This keeps the raw payload, the reason it failed, and enough metadata to
inspect the message in Kafka UI or replay it after a fix, instead of losing it
at the validation boundary. The consumer still commits the original topic
offset after routing a message to the DLQ, so a poison message never blocks
the pipeline.

`src.consumer.main.process_message` contains the routing decision (save /
duplicate / send to DLQ) as a plain function that takes a repository and a DLQ
producer as arguments, so it is unit tested with mocks in
`tests/unit/test_consumer.py` without needing Kafka or PostgreSQL.

## Crash Recovery and Idempotency

The consumer loop in `src.consumer.main.main` does the DB write before the
Kafka offset commit:

```python
process_message(message, ...)  # writes to PostgreSQL
kafka_consumer.commit()        # only then advances the Kafka offset
```

That ordering is deliberate, but it has a consequence: if the process crashes
*after* the write and *before* the commit, Kafka still thinks the message is
unacknowledged. On restart, the consumer group is reassigned the same offset
and receives that message again — Kafka's at-least-once delivery guarantee.
Without protection, the same event would be written to PostgreSQL twice.

This is exactly what `events.event_id UUID NOT NULL UNIQUE` is for. When the
redelivered message reaches `process_message` a second time, `repository.save`
raises `IntegrityError` on the unique constraint, which is caught and treated
as a duplicate rather than crashing the consumer or double-counting the event:

```python
consumer.process_message(event)  # -> "saved",    1 row in PostgreSQL
consumer.process_message(event)  # -> "duplicate", still 1 row in PostgreSQL
```

`tests/consumer/test_idempotency.py` exercises this against a real PostgreSQL
connection: it calls `process_message` with the same event twice and asserts
`events` still contains exactly one row for that `event_id`.

## Out-of-Order and Missing Sequence Detection

Every `Event` also carries a `sequence_id`: a counter kept per `device_id` in
the generator, incremented each time that specific device produces a reading.
Two devices' counters are independent, and because `event_time` is not the
same thing as `sequence_id`, the generator's existing `future_event` and
`old_event` defects already model devices whose clock is wrong while their
sequence counter keeps climbing normally — a realistic IoT failure mode.

`src.quality.sequence_analysis.analyze_sequences` takes `(device_id,
sequence_id)` pairs and, per device, reports:

- **missing** — gaps in the contiguous range between the lowest and highest
  sequence seen (for example, an event the consumer rejected and routed to
  the DLQ instead of storing).
- **duplicates** — a sequence number that shows up more than once.
- Arrival order is irrelevant to this analysis: sequence `[1, 2, 4, 3]` is
  reported as complete, because IDs 1-4 are all present, even though 3 and 4
  arrived out of order.

This is pure, dependency-free logic and is unit tested directly in
`tests/unit/test_sequence_analysis.py` — no infrastructure required. To run it
against real data:

```powershell
python -m src.quality.sequence_report
```

```text
sensor-04: received 2, expected 3, missing [144], duplicates []
```

The script queries `(device_id, sequence_id)` from PostgreSQL, runs the
analysis per device, prints one line per device, and exits with status `1` if
any device has a gap or a duplicate. Note that because the consumer already
deduplicates on `event_id` (see above), a duplicate `sequence_id` reaching
PostgreSQL is expected to be rare in steady state — the check still guards
against it as a second, independent line of defense.

## 2. Start the Infrastructure

Start PostgreSQL, Kafka, Kafka UI, and MinIO:

```powershell
docker compose up -d
```

Check the container status:

```powershell
docker compose ps
```

All services should have the `Up` status. On the first run, PostgreSQL
automatically creates the `events` table.

Available services:

| Service | Address |
| --- | --- |
| PostgreSQL | `localhost:5432` |
| Kafka | `localhost:9092` |
| Kafka UI | http://localhost:8080 |
| MinIO API | `localhost:9000` |
| MinIO Console | http://localhost:9001 |

## 3. Start the Consumer

Activate the virtual environment and start the consumer in the first terminal:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.consumer.main
```

The consumer waits for Kafka messages. No console output before new messages
arrive is expected behavior.

## 4. Start the Generator

Open a second terminal:

```powershell
.\venv\Scripts\Activate.ps1
python -m src.generator.main
```

The generator creates one event per second and sends it to the `events` Kafka
topic. By default, 5% of events are intentionally corrupted. Possible defects
include null or out-of-range measurements, an empty device ID, future or old
timestamps, and duplicates.

The generator terminal will display the created events:

```text
{"device_id":"device-1","event_time":"...","temperature":...}
```

The consumer terminal will display a confirmation after each successful insert:

```text
Saved event: {"device_id":"device-1", ...}
```

This confirms that the message was received from Kafka and stored in PostgreSQL.

Press `Ctrl+C` to stop the generator or consumer.

## 5. Check PostgreSQL

Display the ten most recent records:

```powershell
docker compose exec postgres psql -U postgres -d dataqa -c "SELECT * FROM events ORDER BY id DESC LIMIT 10;"
```

Count all records:

```powershell
docker compose exec postgres psql -U postgres -d dataqa -c "SELECT COUNT(*) FROM events;"
```

Open an interactive PostgreSQL console:

```powershell
docker compose exec postgres psql -U postgres -d dataqa
```

Run a query inside `psql`:

```sql
SELECT * FROM events ORDER BY id DESC LIMIT 10;
```

Run `\q` to exit `psql`.

## 6. Check Kafka

Open Kafka UI:

http://localhost:8080

Then navigate to:

```text
local -> Topics -> events -> Messages
```

This page displays the messages sent by the generator.

## Configuration

The application uses the following default values:

| Variable | Default value |
| --- | --- |
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` |
| `KAFKA_TOPIC` | `events` |
| `KAFKA_DLQ_TOPIC` | `events-dlq` |
| `KAFKA_CONSUMER_GROUP` | `events-consumer` |
| `GENERATOR_INVALID_PROBABILITY` | `0.05` |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/dataqa` |

Override them before starting an application when necessary:

```powershell
$env:KAFKA_TOPIC = "events"
$env:KAFKA_CONSUMER_GROUP = "events-consumer-local"
python -m src.consumer.main
```

`GENERATOR_INVALID_PROBABILITY` must be between `0` and `1`. Set it to `0` for
only valid events or to `1` to corrupt every generated event.

```powershell
$env:GENERATOR_INVALID_PROBABILITY = "0.05"
python -m src.generator.main
```

## Stop the Infrastructure

Stop the containers:

```powershell
docker compose down
```

PostgreSQL data is stored in a Docker volume and remains available after the
next startup.

Remove the containers and all stored data:

```powershell
docker compose down -v
```

The `-v` option permanently removes local PostgreSQL and MinIO data.

## Project Structure

```text
src/
  common/
    config.py          # Application configuration
    database.py        # SQLAlchemy engine and sessions
    models.py          # Shared Pydantic Event model
  generator/
    generator.py       # Event generation
    producer.py        # Sending events to Kafka
    main.py            # Generator entry point
  consumer/
    kafka_consumer.py  # Receiving messages from Kafka
    database_models.py # SQLAlchemy model for the events table
    repository.py      # Persisting events
    dlq.py             # Publishing invalid messages to events-dlq
    main.py            # Consumer entry point / process_message routing
  quality/
    checks.py             # Declarative Check/CheckResult building blocks
    dsl.py                # Table/expect DSL built on top of checks.py
    reconciliation.py     # Pure source-vs-target event_id comparison
    reconcile.py          # Reads Kafka + PostgreSQL and runs reconciliation
    sequence_analysis.py  # Pure per-device missing/duplicate sequence detection
    sequence_report.py    # Reads PostgreSQL and runs the sequence analysis
tests/
  unit/
    test_generator.py
    test_quality_dsl.py
    test_reconciliation.py
    test_consumer.py
    test_sequence_analysis.py
  consumer/
    test_idempotency.py
  schema/
    test_columns.py
  quality/
    test_no_nulls.py
    test_duplicates.py
    test_ranges.py
    test_freshness.py
  business/
    test_device_count.py
    test_status_distribution.py
```
