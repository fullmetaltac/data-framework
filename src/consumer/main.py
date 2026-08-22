from typing import Any

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError

from src.common.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_DLQ_TOPIC,
    KAFKA_TOPIC,
)
from src.common.models import Event
from src.consumer.dlq import DeadLetterProducer
from src.consumer.kafka_consumer import EventKafkaConsumer
from src.consumer.repository import EventRepository


def process_message(
    message: dict[str, Any],
    *,
    repository: EventRepository,
    dlq_producer: DeadLetterProducer,
    source_topic: str,
) -> str:
    try:
        event = Event(**message)
    except ValidationError as error:
        dlq_producer.send(
            original_message=message, error=str(error), source_topic=source_topic
        )
        print(f"Invalid event sent to DLQ: {error}")
        return "invalid"

    try:
        repository.save(event)
    except IntegrityError:
        print(f"Duplicate event skipped: {event.event_id}")
        return "duplicate"

    print(f"Saved event: {event.model_dump_json()}")
    return "saved"


def main() -> None:
    kafka_consumer = EventKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC,
        group_id=KAFKA_CONSUMER_GROUP,
    )
    repository = EventRepository()
    dlq_producer = DeadLetterProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_DLQ_TOPIC,
    )

    kafka_consumer.connect()

    try:
        while True:
            message = kafka_consumer.poll()
            process_message(
                message,
                repository=repository,
                dlq_producer=dlq_producer,
                source_topic=KAFKA_TOPIC,
            )
            kafka_consumer.commit()
    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        kafka_consumer.close()
        dlq_producer.close()


if __name__ == "__main__":
    main()
