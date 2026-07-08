import os
import time

from .generator import EventGenerator
from .producer import EventProducer


def main() -> None:
    generator = EventGenerator()
    producer = EventProducer(
        bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
        topic=os.getenv("KAFKA_TOPIC", "events"),
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
