"""Test application recovery, feedback and continued use after domain errors."""

from datetime import datetime, timedelta, timezone

import pytest

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_comparator import OddsComparator
from odds_explorer import OddsExplorer
from odds_history import OddsHistory
from sample_odds_provider import SampleOddsProvider


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
AS_OF = datetime(2026, 9, 25, 19, 15, tzinfo=timezone.utc)


class TestOddsExplorer:
    @pytest.fixture
    def scenario(self):
        match = Fixture("F001", "Liverpool", "Arsenal", KICKOFF)
        other_match = Fixture("F002", "Chelsea", "Everton", KICKOFF)
        bookmaker_a = Bookmaker("A", "Sample Sports")
        bookmaker_b = Bookmaker("B", "Demo Markets")
        first = MarketSnapshot(match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5)
        second = MarketSnapshot(
            match, bookmaker_b, RECORDED_AT + timedelta(minutes=2), 2.3, 3.3, 3.4
        )
        history = OddsHistory(match)
        history.add_snapshot(first)
        history.add_snapshot(second)
        comparator = OddsComparator(10)
        return {
            "explorer": OddsExplorer(history, comparator),
            "history": history, "comparator": comparator,
            "first": first, "second": second,
            "wrong_fixture": MarketSnapshot(
                other_match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5
            ),
            "lookalike": MarketSnapshot(
                match, bookmaker_a, RECORDED_AT, 2.2, 3.4, 3.5
            ),
        }

    @pytest.mark.parametrize("outcome", ["home", "draw", "away"])
    def test_invalid_load_reports_error_and_allows_valid_load(
        self, scenario, capsys, outcome
    ):
        explorer, history = scenario["explorer"], scenario["history"]
        first = scenario["first"]
        original = history.snapshots
        original_quotes = first.quotes
        prices = {"home": 2.2, "draw": 3.4, "away": 3.5}
        prices[outcome] = 0.5
        provider = SampleOddsProvider(
            first.fixture, first.bookmaker, RECORDED_AT, **prices
        )

        assert explorer.load_snapshot(provider) is None
        feedback = capsys.readouterr().out
        assert "Snapshot not loaded:" in feedback
        assert f"Invalid {outcome} odds 0.5" in feedback
        assert history.snapshots == original
        assert first.quotes == original_quotes

        valid_provider = SampleOddsProvider(
            first.fixture, first.bookmaker, RECORDED_AT, 2.2, 3.4, 3.5
        )
        loaded = explorer.load_snapshot(valid_provider)
        assert loaded.is_complete() is True
        assert explorer.add_snapshot(loaded) is True
        assert history.snapshots == original + [loaded]
        assert capsys.readouterr().out == ""

    @pytest.mark.parametrize("outcome", ["unknown", None, []])
    def test_unknown_quote_reports_error_and_preserves_quotes(
        self, scenario, capsys, outcome
    ):
        explorer, first = scenario["explorer"], scenario["first"]
        original = first.quotes

        assert explorer.get_quote(first, outcome) is None
        feedback = capsys.readouterr().out
        assert "Quote lookup failed:" in feedback
        assert repr(outcome) in feedback
        assert "home, draw or away" in feedback
        assert first.quotes == original
        assert explorer.get_quote(first, "home") is original["home"]

    @pytest.mark.parametrize("snapshot_key, reason", [
        ("wrong_fixture", "F002"), ("first", "already stored"),
    ])
    def test_rejected_addition_keeps_history_and_allows_valid_addition(
        self, scenario, capsys, snapshot_key, reason
    ):
        explorer, history = scenario["explorer"], scenario["history"]
        original = history.snapshots

        assert explorer.add_snapshot(scenario[snapshot_key]) is False
        feedback = capsys.readouterr().out
        assert "Snapshot not added:" in feedback
        assert reason in feedback
        assert "F001" in feedback
        assert history.snapshots == original
        assert explorer.add_snapshot(scenario["lookalike"]) is True
        assert history.snapshots == original + [scenario["lookalike"]]

    def test_missing_removal_keeps_history_and_allows_later_updates(
        self, scenario, capsys
    ):
        explorer, history = scenario["explorer"], scenario["history"]
        first, second = scenario["first"], scenario["second"]

        assert explorer.remove_snapshot(scenario["lookalike"]) is False
        feedback = capsys.readouterr().out
        assert "Snapshot not removed:" in feedback
        assert "not stored" in feedback
        assert "Sample Sports" in feedback and str(RECORDED_AT) in feedback
        assert history.snapshots == [first, second]
        assert explorer.remove_snapshot(first) is True
        assert history.snapshots == [second]
        assert explorer.remove_snapshot(first) is False
        assert "not stored" in capsys.readouterr().out
        assert history.snapshots == [second]
        assert explorer.add_snapshot(first) is True
        assert history.snapshots == [second, first]

    @pytest.mark.parametrize("second_key, outcome, reason", [
        ("wrong_fixture", "home", "F002"),
        ("second", "unknown", "Unknown outcome 'unknown'"),
    ])
    def test_invalid_comparison_reports_error_and_allows_valid_comparison(
        self, scenario, capsys, second_key, outcome, reason
    ):
        explorer, history = scenario["explorer"], scenario["history"]
        first, other = scenario["first"], scenario[second_key]
        original = history.snapshots
        original_quotes = (first.quotes, other.quotes)

        assert explorer.compare(first, other, outcome, AS_OF) is None
        feedback = capsys.readouterr().out
        assert "Comparison failed:" in feedback
        assert reason in feedback
        assert history.snapshots == original
        assert (first.quotes, other.quotes) == original_quotes
        assert explorer.compare(first, scenario["second"], "home", AS_OF) is scenario["second"]

    @pytest.mark.parametrize("value", [-1, True, "10"])
    def test_invalid_age_keeps_old_limit_and_allows_valid_update(
        self, scenario, capsys, value
    ):
        explorer, comparator = scenario["explorer"], scenario["comparator"]
        first, second = scenario["first"], scenario["second"]

        assert explorer.set_maximum_quote_age(value) is False
        feedback = capsys.readouterr().out
        assert "Quote age limit not changed:" in feedback
        assert repr(value) in feedback
        assert "minutes" in feedback
        assert comparator.maximum_quote_age == 10
        assert explorer.compare(first, second, "home", AS_OF) is second
        assert explorer.set_maximum_quote_age(2) is True
        assert comparator.maximum_quote_age == 2
        assert explorer.compare(
            first, second, "home", RECORDED_AT + timedelta(minutes=1)
        ) is first

    @pytest.mark.parametrize("outcome, start, end, reason", [
        ("home", AS_OF, RECORDED_AT, "start must not be after end"),
        ("unknown", RECORDED_AT, AS_OF, "Unknown outcome 'unknown'"),
    ])
    def test_invalid_price_change_keeps_data_and_allows_valid_calculation(
        self, scenario, capsys, outcome, start, end, reason
    ):
        explorer, history = scenario["explorer"], scenario["history"]
        first = scenario["first"]
        original = history.snapshots
        original_quotes = [snapshot.quotes for snapshot in original]

        assert explorer.price_change(first.bookmaker, outcome, start, end) is None
        feedback = capsys.readouterr().out
        assert "Price change failed:" in feedback
        assert reason in feedback
        assert history.snapshots == original
        assert [snapshot.quotes for snapshot in history.snapshots] == original_quotes
        assert explorer.price_change(
            first.bookmaker, "home", RECORDED_AT, AS_OF
        ) == 0

    def test_ordinary_missing_data_does_not_report_errors(self, scenario, capsys):
        explorer = scenario["explorer"]
        first, second = scenario["first"], scenario["second"]
        incomplete = explorer.load_snapshot(SampleOddsProvider(
            first.fixture, first.bookmaker, RECORDED_AT, None, 3.4, 3.5
        ))

        assert incomplete.is_complete() is False
        assert explorer.get_quote(incomplete, "home").decimal_odds is None
        assert explorer.compare(incomplete, second, "home", AS_OF) is second
        assert explorer.compare(first, second, "home", KICKOFF) is None
        empty = OddsExplorer(OddsHistory(first.fixture), scenario["comparator"])
        assert empty.price_change(first.bookmaker, "home", RECORDED_AT, AS_OF) is None
        assert capsys.readouterr().out == ""

    def test_unexpected_provider_error_is_not_hidden(self, scenario):
        class BrokenProvider:
            def load_snapshot(self):
                raise RuntimeError("Unexpected provider bug")

        with pytest.raises(RuntimeError, match="Unexpected provider bug"):
            scenario["explorer"].load_snapshot(BrokenProvider())
