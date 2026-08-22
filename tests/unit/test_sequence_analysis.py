from src.quality.sequence_analysis import analyze_sequences


def test_contiguous_sequence_passes() -> None:
    readings = [("sensor-01", 1), ("sensor-01", 2), ("sensor-01", 3)]

    reports = analyze_sequences(readings)

    assert len(reports) == 1
    report = reports[0]
    assert report.passed
    assert report.received_count == 3
    assert report.expected_count == 3
    assert not report.missing
    assert not report.duplicates


def test_detects_missing_sequences() -> None:
    readings = [("sensor-04", 143), ("sensor-04", 145)]

    report = analyze_sequences(readings)[0]

    assert not report.passed
    assert report.missing == (144,)
    assert report.expected_count == 3
    assert report.received_count == 2


def test_detects_duplicate_sequences() -> None:
    readings = [("sensor-02", 1), ("sensor-02", 2), ("sensor-02", 2)]

    report = analyze_sequences(readings)[0]

    assert not report.passed
    assert report.duplicates == (2,)
    assert not report.missing


def test_out_of_order_arrival_does_not_affect_gap_detection() -> None:
    readings = [("sensor-09", 1), ("sensor-09", 2), ("sensor-09", 4), ("sensor-09", 3)]

    report = analyze_sequences(readings)[0]

    assert report.passed
    assert not report.missing


def test_devices_are_analyzed_independently() -> None:
    readings = [("sensor-01", 1), ("sensor-01", 3), ("sensor-02", 1), ("sensor-02", 2)]

    reports = {report.device_id: report for report in analyze_sequences(readings)}

    assert reports["sensor-01"].missing == (2,)
    assert reports["sensor-02"].passed
