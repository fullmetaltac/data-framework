import json
from datetime import datetime, timezone
from typing import Any

from kafka import KafkaProducer


class DeadLetterProducer:
    def __init__(self, bootstrap_servers: str, topic: str) -> None:
        self._topic = topic
        self._producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        )

    def send(
        self, *, original_message: dict[str, Any], error: str, source_topic: str
    ) -> None:
        payload = {
            "original_message": original_message,
            "error": error,
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "source_topic": source_topic,
        }
        self._producer.send(self._topic, value=payload).get(timeout=10)

    def close(self) -> None:
        self._producer.flush()
        self._producer.close()
