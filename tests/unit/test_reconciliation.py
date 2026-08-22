from uuid import uuid4

from src.quality.reconciliation import reconcile


def test_matching_sources_and_targets_pass() -> None:
    ids = [uuid4() for _ in range(5)]

    result = reconcile(ids, ids)

    assert result.passed
    assert result.source_count == 5
    assert result.target_count == 5
    assert not result.missing
    assert not result.duplicates
    assert not result.unexpected


def test_detects_missing_events() -> None:
    ids = [uuid4() for _ in range(3)]
    missing_id = ids[1]

    result = reconcile(ids, [event_id for event_id in ids if event_id != missing_id])

    assert not result.passed
    assert result.missing == {missing_id}
    assert not result.unexpected


def test_detects_duplicate_source_events() -> None:
    duplicate_id = uuid4()
    ids = [duplicate_id, duplicate_id, uuid4()]

    result = reconcile(ids, [duplicate_id, uuid4()])

    assert result.duplicates == {duplicate_id}


def test_detects_unexpected_target_events() -> None:
    ids = [uuid4() for _ in range(2)]
    unexpected_id = uuid4()

    result = reconcile(ids, [*ids, unexpected_id])

    assert not result.passed
    assert result.unexpected == {unexpected_id}
