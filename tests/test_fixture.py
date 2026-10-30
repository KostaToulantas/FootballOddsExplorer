"""Test the exclusive kickoff boundary and fixture display."""

from datetime import datetime, timedelta, timezone

import pytest

from fixture import Fixture


KICKOFF = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)


class TestFixture:
    @pytest.fixture
    def match(self):
        return Fixture("F001", "Liverpool", "Arsenal", KICKOFF)

    def test_before_kickoff(self, match):
        assert match.is_before_kickoff(KICKOFF - timedelta(minutes=10)) is True
        assert match.is_before_kickoff(
            KICKOFF - timedelta(microseconds=1)) is True

    def test_at_and_after_kickoff(self, match):
        assert match.is_before_kickoff(KICKOFF) is False
        assert match.is_before_kickoff(
            KICKOFF + timedelta(microseconds=1)) is False

    def test_string(self, match):
        assert str(match) == (
            "Liverpool vs Arsenal (kickoff: 2026-09-25 19:30:00+00:00)"
        )
