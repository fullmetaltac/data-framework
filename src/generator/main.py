import logging
import time

from src.common.config import (
    GENERATOR_INVALID_PROBABILITY,
    KAFKA_BOOTSTRAP_SERVERS,
    KAFKA_TOPIC,
)
from src.common.logging_config import configure_logging

from .generator import EventGenerator
from .producer import EventProducer

logger = logging.getLogger(__name__)


def main() -> None:
    configure_logging()

    generator = EventGenerator(
        invalid_probability=GENERATOR_INVALID_PROBABILITY,
    )
    producer = EventProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        topic=KAFKA_TOPIC,
    )

    try:
        while True:
            event = generator.generate()
            producer.send(event)
            logger.info(event.model_dump_json())
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Generator stopped.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()
