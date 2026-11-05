"""Test history updates, filtering, time selection, and price changes."""

from datetime import datetime, timedelta, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_exceptions import (
    DuplicateSnapshotError, FixtureMismatchError, InvalidTimeRangeError,
    SnapshotNotFoundError, UnknownOutcomeError,
)
from odds_history import OddsHistory


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)


class TestOddsHistory:
    @pytest.fixture
    def bookmaker(self):
        return Bookmaker("A", "Sample Sports")

    @pytest.fixture
    def renamed_bookmaker(self):
        return Bookmaker("A", "Renamed Sports")

    @pytest.fixture
    def other_bookmaker(self):
        return Bookmaker("B", "Demo Markets")

    @pytest.fixture
    def unknown_bookmaker(self):
        return Bookmaker("C", "Unknown")

    @pytest.fixture
    def empty_history(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        return OddsHistory(match)

    @pytest.fixture
    def history_data(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker_a = Bookmaker("A", "Sample Sports")
        bookmaker_b = Bookmaker("B", "Demo Markets")
        earlier = MarketSnapshot(
            match, bookmaker_a, RECORDED_AT -
            timedelta(minutes=20), 2.1, 3.4, 3.6
        )
        first = MarketSnapshot(match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5)
        second = MarketSnapshot(
            match, bookmaker_b, RECORDED_AT +
            timedelta(minutes=2), 2.3, 3.3, 3.4
        )
        third = MarketSnapshot(
            match, bookmaker_a, RECORDED_AT +
            timedelta(minutes=10), 2.2, 3.3, 3.6
        )
        history = OddsHistory(match)
        # Unsorted records check that time queries use timestamps.
        history.add_snapshot(third)
        history.add_snapshot(first)
        history.add_snapshot(second)
        history.add_snapshot(earlier)
        return {
            "history": history, "bookmaker_a": bookmaker_a,
            "earlier": earlier, "first": first,
            "second": second, "third": third,
        }

    @pytest.fixture
    def new_snapshot(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return MarketSnapshot(match, bookmaker, RECORDED_AT, 2.2, 3.4, 3.5)

    @pytest.fixture
    def wrong_fixture_snapshot(self):
        match = Fixture("F002", "Chelsea", "Everton", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        return MarketSnapshot(match, bookmaker, RECORDED_AT, 2.2, 3.4, 3.5)

    @pytest.fixture
    def incomplete_history(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        bookmaker = Bookmaker("A", "Sample Sports")
        history = OddsHistory(match)
        history.add_snapshot(MarketSnapshot(
            match, bookmaker, RECORDED_AT, None, 3.4, 3.5
        ))
        history.add_snapshot(MarketSnapshot(
            match, bookmaker, RECORDED_AT +
            timedelta(minutes=5), 2.2, None, 3.5
        ))
        history.add_snapshot(MarketSnapshot(
            match, bookmaker, RECORDED_AT +
            timedelta(minutes=10), None, 3.3, 3.5
        ))
        return history

    def test_new_history_is_empty(
        self, empty_history, new_snapshot, bookmaker
    ):
        assert empty_history.snapshots == []
        assert empty_history.has_snapshot(new_snapshot) is False
        assert empty_history.filter_by_bookmaker(bookmaker) == []
        assert empty_history.snapshots_at(bookmaker, RECORDED_AT) == []
        assert empty_history.latest_at(bookmaker, RECORDED_AT) is None
        assert empty_history.price_change(
            bookmaker, "home", RECORDED_AT, RECORDED_AT
        ) is None

    def test_add_snapshot(self, empty_history, new_snapshot):
        # The fixture objects are separate, but share the same fixture ID.
        assert empty_history.add_snapshot(new_snapshot) is True
        assert empty_history.has_snapshot(new_snapshot) is True
        assert empty_history.snapshots == [new_snapshot]

    def test_duplicate_object_is_rejected(self, history_data):
        history = history_data["history"]
        original = history.snapshots
        first = history_data["first"]
        with pytest.raises(DuplicateSnapshotError) as caught:
            history.add_snapshot(first)

        message = str(caught.value)
        assert "F001" in message
        assert "Sample Sports" in message
        assert str(first.recorded_at) in message
        assert history.snapshots == original

    def test_distinct_object_is_accepted(self, history_data, new_snapshot):
        history = history_data["history"]
        assert history.has_snapshot(new_snapshot) is False
        assert history.add_snapshot(new_snapshot) is True
        assert len(history.snapshots) == 5
        assert history.snapshots[-1] is new_snapshot

    def test_invalid_additions_do_not_change_history(
        self, history_data, wrong_fixture_snapshot
    ):
        history = history_data["history"]
        original = history.snapshots
        assert history.add_snapshot(None) is False
        assert history.add_snapshot("snapshot") is False
        with pytest.raises(FixtureMismatchError) as caught:
            history.add_snapshot(wrong_fixture_snapshot)

        message = str(caught.value)
        assert "add snapshot to history" in message
        assert "F001" in message and "F002" in message
        assert history.snapshots == original
        assert not history.has_snapshot(wrong_fixture_snapshot)

    def test_insertion_order_and_repeated_prices(
        self, empty_history, history_data
    ):
        snapshots = [
            history_data["third"], history_data["first"],
            history_data["second"], history_data["earlier"],
        ]
        for snapshot in snapshots:
            assert empty_history.add_snapshot(snapshot) is True

        assert empty_history.snapshots == snapshots

    def test_remove_snapshot(self, history_data, new_snapshot):
        history = history_data["history"]
        first = history_data["first"]
        original = history.snapshots
        with pytest.raises(SnapshotNotFoundError) as caught:
            history.remove_snapshot(new_snapshot)

        message = str(caught.value)
        assert "F001" in message
        assert "Sample Sports" in message
        assert str(new_snapshot.recorded_at) in message
        assert history.snapshots == original
        assert history.remove_snapshot(first) is True
        assert history.has_snapshot(first) is False
        assert history.snapshots == [
            history_data["third"], history_data["second"],
            history_data["earlier"]
        ]
        after_removal = history.snapshots
        with pytest.raises(SnapshotNotFoundError, match="not stored"):
            history.remove_snapshot(first)
        assert history.snapshots == after_removal
        assert history.remove_snapshot(None) is False
        assert history.add_snapshot(first) is True
        assert history.snapshots == after_removal + [first]

    def test_external_list_changes(self, history_data, new_snapshot):
        history = history_data["history"]
        original = history.snapshots
        snapshots = history.snapshots
        snapshots.reverse()
        snapshots.append(new_snapshot)
        snapshots.clear()

        assert history.snapshots == original
        assert history.has_snapshot(new_snapshot) is False

    def test_filter_by_bookmaker(
        self, history_data, renamed_bookmaker, other_bookmaker,
        unknown_bookmaker
    ):
        history = history_data["history"]
        # A different name still matches when the bookmaker ID is the same.
        expected = [
            history_data["third"], history_data["first"],
            history_data["earlier"]
        ]
        result = history.filter_by_bookmaker(renamed_bookmaker)
        assert result == expected
        result.clear()
        assert history.filter_by_bookmaker(renamed_bookmaker) == expected
        assert history.filter_by_bookmaker(other_bookmaker) == [
            history_data["second"]
        ]
        assert history.filter_by_bookmaker(unknown_bookmaker) == []

    def test_snapshots_at_includes_cutoff(self, history_data):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        assert history.snapshots_at(
            bookmaker, RECORDED_AT - timedelta(minutes=21)
        ) == []
        assert history.snapshots_at(
            bookmaker, RECORDED_AT - timedelta(minutes=20)
        ) == [history_data["earlier"]]
        expected = [history_data["first"], history_data["earlier"]]
        assert history.snapshots_at(bookmaker, RECORDED_AT) == expected
        result = history.snapshots_at(
            bookmaker, RECORDED_AT + timedelta(minutes=5))
        assert result == expected
        result.clear()
        assert history.snapshots_at(bookmaker, RECORDED_AT) == expected
        assert history.snapshots_at(
            bookmaker, RECORDED_AT + timedelta(minutes=10)
        ) == [
            history_data["third"], history_data["first"],
            history_data["earlier"]
        ]

    def test_latest_at_uses_timestamp(self, history_data, unknown_bookmaker):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        assert history.latest_at(
            bookmaker, RECORDED_AT - timedelta(minutes=21)
        ) is None
        assert history.latest_at(
            bookmaker, RECORDED_AT - timedelta(minutes=20)
        ) is history_data["earlier"]
        assert history.latest_at(
            bookmaker, RECORDED_AT) is history_data["first"]
        assert history.latest_at(
            bookmaker, RECORDED_AT + timedelta(minutes=5)
        ) is history_data["first"]
        assert history.latest_at(
            bookmaker, RECORDED_AT + timedelta(minutes=15)
        ) is history_data["third"]
        assert history.latest_at(unknown_bookmaker, KICKOFF) is None

    def test_equal_latest_timestamps(self, history_data, new_snapshot):
        history = history_data["history"]
        assert history.add_snapshot(new_snapshot) is True
        assert history.latest_at(
            history_data["bookmaker_a"], RECORDED_AT
        ) is history_data["first"]

    def test_price_changes(self, history_data):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        start = RECORDED_AT - timedelta(minutes=19)
        end = RECORDED_AT + timedelta(minutes=5)
        assert history.price_change(
            bookmaker, "home", start, end) == pytest.approx(0.1)
        assert history.price_change(
            bookmaker, "away", start, end) == pytest.approx(-0.1)
        assert history.price_change(
            bookmaker, "draw", start, end) == pytest.approx(0)

    def test_same_time_or_record_has_zero_price_change(self, history_data):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        assert history.price_change(
            bookmaker, "home", RECORDED_AT, RECORDED_AT
        ) == pytest.approx(0)
        assert history.price_change(
            bookmaker, "home", RECORDED_AT + timedelta(minutes=1),
            RECORDED_AT + timedelta(minutes=2)
        ) == pytest.approx(0)

    def test_price_change_missing_data(
        self, history_data, unknown_bookmaker
    ):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        end = RECORDED_AT + timedelta(minutes=5)
        assert history.price_change(
            bookmaker, "home", RECORDED_AT - timedelta(minutes=21), end
        ) is None
        assert history.price_change(
            unknown_bookmaker, "home", RECORDED_AT, end
        ) is None

    def test_reversed_price_change_interval_raises(self, history_data):
        history = history_data["history"]
        bookmaker = history_data["bookmaker_a"]
        original = history.snapshots
        start = RECORDED_AT + timedelta(minutes=5)
        end = RECORDED_AT
        with pytest.raises(InvalidTimeRangeError) as caught:
            history.price_change(bookmaker, "home", start, end)

        message = str(caught.value)
        assert str(start) in message and str(end) in message
        assert "start must not be after end" in message
        assert history.snapshots == original
        assert history.price_change(bookmaker, "home", end, start) == 0

    @pytest.mark.parametrize("outcome", ["unknown", "HOME", None, []])
    def test_unknown_price_change_outcome_raises_even_without_records(
        self, history_data, empty_history, outcome
    ):
        bookmaker = history_data["bookmaker_a"]
        for history in [history_data["history"], empty_history]:
            original = history.snapshots
            original_quotes = [snapshot.quotes for snapshot in original]
            with pytest.raises(UnknownOutcomeError) as caught:
                history.price_change(bookmaker, outcome, RECORDED_AT, RECORDED_AT)

            assert repr(outcome) in str(caught.value)
            assert "home, draw or away" in str(caught.value)
            assert history.snapshots == original
            assert [snapshot.quotes for snapshot in history.snapshots] == original_quotes
        assert history_data["history"].price_change(
            bookmaker, "home", RECORDED_AT, RECORDED_AT
        ) == 0

    def test_unavailable_endpoint_prices_have_no_change(
        self, incomplete_history, bookmaker
    ):
        middle = RECORDED_AT + timedelta(minutes=5)
        end = RECORDED_AT + timedelta(minutes=10)
        assert incomplete_history.price_change(
            bookmaker, "home", RECORDED_AT, middle
        ) is None
        assert incomplete_history.price_change(
            bookmaker, "home", middle, end) is None
        assert incomplete_history.price_change(
            bookmaker, "home", RECORDED_AT, end
        ) is None

    def test_valid_outcome_in_incomplete_market(
        self, incomplete_history, bookmaker
    ):
        assert len(incomplete_history.snapshots) == 3
        assert incomplete_history.price_change(
            bookmaker, "draw", RECORDED_AT, RECORDED_AT + timedelta(minutes=10)
        ) == pytest.approx(-0.1)

    def test_string_count_tracks_changes(self, empty_history, new_snapshot):
        prefix = (
            "History for Liverpool vs Arsenal "
            "(kickoff: 2026-09-25 19:30:00+00:00): "
        )
        assert str(empty_history) == prefix + "0 snapshots"
        assert empty_history.add_snapshot(new_snapshot) is True
        assert str(empty_history) == prefix + "1 snapshots"
        assert empty_history.remove_snapshot(new_snapshot) is True
        assert str(empty_history) == prefix + "0 snapshots"
