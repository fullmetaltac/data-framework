from kafka import KafkaProducer

from src.common.models import Event


class EventProducer:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._topic = topic
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: value.encode("utf-8"),
        )

    def send(self, event: Event) -> None:
        payload = event.model_dump_json()
        self._producer.send(self._topic, value=payload).get(timeout=10)

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()
