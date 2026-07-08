import json
from typing import Any

from kafka import KafkaConsumer


class EventKafkaConsumer:
    def __init__(self, bootstrap_servers: str, topic: str, group_id: str) -> None:
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._consumer: KafkaConsumer | None = None

    def connect(self) -> None:
        self._consumer = KafkaConsumer(
            self._topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset="earliest",
            enable_auto_commit=False,
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )

    def poll(self) -> dict[str, Any]:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not connected.")

        message = next(self._consumer)
        return message.value

    def commit(self) -> None:
        if self._consumer is None:
            raise RuntimeError("Kafka consumer is not connected.")

        self._consumer.commit()

    def close(self) -> None:
        if self._consumer is not None:
            self._consumer.close()
            self._consumer = None
