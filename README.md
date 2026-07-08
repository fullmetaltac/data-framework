# Data Framework

A small data pipeline for generating and storing events:

```text
Generator -> Kafka -> Consumer -> PostgreSQL
```

The generator creates events and sends them to Kafka. The consumer receives the
messages, validates them using the Pydantic `Event` model, and stores them in the
`events` table through SQLAlchemy.

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
topic.

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
| `KAFKA_CONSUMER_GROUP` | `events-consumer` |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/dataqa` |

Override them before starting an application when necessary:

```powershell
$env:KAFKA_TOPIC = "events"
$env:KAFKA_CONSUMER_GROUP = "events-consumer-local"
python -m src.consumer.main
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
    main.py            # Consumer entry point
```
