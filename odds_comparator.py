from datetime import timedelta

from market_snapshot import MarketSnapshot


class OddsComparator:
    """Compare markets at a datetime, with maximum quote age in minutes."""

    def __init__(self, maximum_quote_age):
        self.__maximum_quote_age = 0
        self.maximum_quote_age = maximum_quote_age

    def get_maximum_quote_age(self):
        return self.__maximum_quote_age

    def set_maximum_quote_age(self, value):
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
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
        """Return the winning snapshot: the first wins ties. None means no result."""
        if not isinstance(first, MarketSnapshot) or not isinstance(second, MarketSnapshot):
            return None
        if first.fixture.fixture_id != second.fixture.fixture_id:
            return None
        first_quote = first.get_quote(outcome)
        second_quote = second.get_quote(outcome)
        if first_quote is None or second_quote is None:
            return None
        best = None
        if self.is_eligible(first, as_of):
            best = first
        if self.is_eligible(second, as_of):
            if best is None or second_quote.decimal_odds > first_quote.decimal_odds:
                best = second
        return best
