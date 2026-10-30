"""Test bookmaker equality and string conversion."""

import pytest

from bookmaker import Bookmaker


class TestBookmaker:
    @pytest.fixture
    def bookmaker(self):
        return Bookmaker("A", "Sample Sports")

    @pytest.fixture
    def matching_bookmakers(self):
        return [
            Bookmaker("A", "Sample Sports"),
            Bookmaker("A", "Renamed Sports"),
        ]

    @pytest.fixture
    def different_bookmakers(self):
        return [
            Bookmaker("B", "Demo Markets"),
            Bookmaker("B", "Sample Sports"),
        ]

    def test_same_id_is_equal(self, bookmaker, matching_bookmakers):
        assert bookmaker == matching_bookmakers[0]
        assert bookmaker == matching_bookmakers[1]

    def test_different_id_is_not_equal(self, bookmaker, different_bookmakers):
        assert bookmaker != different_bookmakers[0]
        assert bookmaker != different_bookmakers[1]

    def test_other_types_are_not_equal(self, bookmaker):
        assert bookmaker != "A"
        assert bookmaker != 1

    def test_string(self, bookmaker):
        assert str(bookmaker) == "Sample Sports"
