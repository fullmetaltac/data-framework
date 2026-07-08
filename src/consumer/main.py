from pydantic import ValidationError

from src.common.config import (
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_CONSUMER_GROUP,
    KAFKA_TOPIC,
)
from src.common.models import Event
from src.consumer.kafka_consumer import EventKafkaConsumer
from src.consumer.repository import EventRepository


def main() -> None:
    kafka_consumer = EventKafkaConsumer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC,
        group_id=KAFKA_CONSUMER_GROUP,
    )
    repository = EventRepository()

    kafka_consumer.connect()

    try:
        while True:
            message = kafka_consumer.poll()

            try:
                event = Event(**message)
            except ValidationError as error:
                print(f"Invalid event skipped: {error}")
                kafka_consumer.commit()
                continue

            repository.save(event)
            kafka_consumer.commit()
            print(f"Saved event: {event.model_dump_json()}")
    except KeyboardInterrupt:
        print("Consumer stopped.")
    finally:
        kafka_consumer.close()


if __name__ == "__main__":
    main()
