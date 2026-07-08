import time

from src.common.config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

from .generator import EventGenerator
from .producer import EventProducer


def main() -> None:
    generator = EventGenerator()
    producer = EventProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC,
    )

    try:
        while True:
            event = generator.generate()
            producer.send(event)
            print(event.model_dump_json())
            time.sleep(1)
    except KeyboardInterrupt:
        print("Generator stopped.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
