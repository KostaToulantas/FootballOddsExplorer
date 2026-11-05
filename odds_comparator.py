from datetime import timedelta

from market_snapshot import MarketSnapshot
from odds_exceptions import FixtureMismatchError, InvalidQuoteAgeError


class OddsComparator:
    """Compare markets at a datetime, with maximum quote age in minutes."""

    def __init__(self, maximum_quote_age):
        self.maximum_quote_age = maximum_quote_age

    def get_maximum_quote_age(self):
        return self.__maximum_quote_age

    def set_maximum_quote_age(self, value):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidQuoteAgeError(value)
        self.__maximum_quote_age = value

    maximum_quote_age = property(get_maximum_quote_age, set_maximum_quote_age)

    def is_eligible(self, snapshot, as_of):
        if not isinstance(snapshot, MarketSnapshot):
            return False
        age = as_of - snapshot.recorded_at
        return (snapshot.is_complete()
                and snapshot.fixture.is_before_kickoff(as_of)
                and timedelta(0) <= age <= timedelta(minutes=self.__maximum_quote_age))

    def compare(self, first, second, outcome, as_of):
        """Return the best eligible snapshot, rejecting mismatched fixtures or keys.

        The first snapshot wins ties. None means no eligible result or an input
        that is not a MarketSnapshot.
        """
        if not isinstance(first, MarketSnapshot) or not isinstance(second, MarketSnapshot):
            return None
        if first.fixture.fixture_id != second.fixture.fixture_id:
            raise FixtureMismatchError(
                "compare snapshots", first.fixture.fixture_id,
                second.fixture.fixture_id
            )
        first_quote = first.get_quote(outcome)
        second_quote = second.get_quote(outcome)
        best = None
        if self.is_eligible(first, as_of):
            best = first
        if self.is_eligible(second, as_of):
            if best is None or second_quote.decimal_odds > first_quote.decimal_odds:
                best = second
        return best
