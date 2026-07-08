import unittest
from datetime import timedelta
from unittest.mock import patch

from src.generator.generator import EventGenerator, InvalidEventType


class EventGeneratorTest(unittest.TestCase):
    def test_rejects_probability_outside_valid_range(self) -> None:
        for probability in (-0.01, 1.01):
            with self.subTest(probability=probability):
                with self.assertRaises(ValueError):
                    EventGenerator(invalid_probability=probability)

    def test_zero_probability_generates_valid_event(self) -> None:
        event = EventGenerator(invalid_probability=0).generate()

        self.assertTrue(event.device_id)
        self.assertIsNotNone(event.temperature)
        self.assertLessEqual(event.humidity, 90)

    def test_each_invalid_event_type(self) -> None:
        generator = EventGenerator(invalid_probability=1)
        generator._last_event = generator._generate_valid_event()

        for error_type in InvalidEventType:
            with self.subTest(error_type=error_type):
                valid_event = generator._generate_valid_event()
                with patch("src.generator.generator.random.choice", return_value=error_type):
                    invalid_event = generator._make_invalid(valid_event)

                if error_type == InvalidEventType.NULL_TEMPERATURE:
                    self.assertIsNone(invalid_event.temperature)
                elif error_type == InvalidEventType.HIGH_HUMIDITY:
                    self.assertEqual(invalid_event.humidity, 150)
                elif error_type == InvalidEventType.LOW_TEMPERATURE:
                    self.assertEqual(invalid_event.temperature, -100)
                elif error_type == InvalidEventType.EMPTY_DEVICE_ID:
                    self.assertEqual(invalid_event.device_id, "")
                elif error_type == InvalidEventType.FUTURE_EVENT:
                    self.assertEqual(
                        invalid_event.event_time,
                        valid_event.event_time + timedelta(days=2),
                    )
                elif error_type == InvalidEventType.DUPLICATE:
                    self.assertEqual(invalid_event, generator._last_event)
                else:
                    self.assertEqual(
                        invalid_event.event_time,
                        valid_event.event_time - timedelta(days=7),
                    )

    def test_duplicate_repeats_previous_event(self) -> None:
        generator = EventGenerator(invalid_probability=1)

        with patch("src.generator.generator.random.choice") as choose_error:
            choose_error.side_effect = [
                InvalidEventType.HIGH_HUMIDITY,
                InvalidEventType.DUPLICATE,
            ]
            first_event = generator.generate()
            second_event = generator.generate()

        self.assertEqual(second_event, first_event)


if __name__ == "__main__":
    unittest.main()
