from collections.abc import Iterator
from datetime import timedelta

import pytest
from pytest import MonkeyPatch

from src.generator.generator import EventGenerator, InvalidEventType


@pytest.mark.parametrize("probability", [-0.01, 1.01])
def test_rejects_probability_outside_valid_range(probability: float) -> None:
    with pytest.raises(
        ValueError,
        match="invalid_probability must be between 0 and 1",
    ):
        EventGenerator(invalid_probability=probability)


def test_zero_probability_generates_valid_event() -> None:
    event = EventGenerator(invalid_probability=0).generate()

    assert event.device_id
    assert event.temperature is not None
    assert event.humidity <= 90


@pytest.mark.parametrize("error_type", list(InvalidEventType))
def test_each_invalid_event_type(
    error_type: InvalidEventType,
    monkeypatch: MonkeyPatch,
) -> None:
    generator = EventGenerator(invalid_probability=1)
    generator._last_event = generator._generate_valid_event()
    valid_event = generator._generate_valid_event()
    monkeypatch.setattr(
        "src.generator.generator.random.choice",
        lambda _: error_type,
    )

    invalid_event = generator._make_invalid(valid_event)

    if error_type == InvalidEventType.NULL_TEMPERATURE:
        assert invalid_event.temperature is None
    elif error_type == InvalidEventType.HIGH_HUMIDITY:
        assert invalid_event.humidity == 150
    elif error_type == InvalidEventType.LOW_TEMPERATURE:
        assert invalid_event.temperature == -100
    elif error_type == InvalidEventType.EMPTY_DEVICE_ID:
        assert invalid_event.device_id == ""
    elif error_type == InvalidEventType.FUTURE_EVENT:
        assert invalid_event.event_time == (valid_event.event_time + timedelta(days=2))
    elif error_type == InvalidEventType.DUPLICATE:
        assert invalid_event == generator._last_event
    else:
        assert invalid_event.event_time == (valid_event.event_time - timedelta(days=7))


def test_duplicate_repeats_previous_event(monkeypatch: MonkeyPatch) -> None:
    generator = EventGenerator(invalid_probability=1)
    error_types: Iterator[InvalidEventType] = iter(
        [
            InvalidEventType.HIGH_HUMIDITY,
            InvalidEventType.DUPLICATE,
        ]
    )
    monkeypatch.setattr(
        "src.generator.generator.random.choice",
        lambda _: next(error_types),
    )

    first_event = generator.generate()
    second_event = generator.generate()

    assert second_event == first_event
