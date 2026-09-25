from market_snapshot import MarketSnapshot


class OddsHistory:

    def __init__(self, fixture):
        self.__fixture = fixture
        self.__first = None
        self.__second = None

    def add_snapshot(self, snapshot):
        if not isinstance(snapshot, MarketSnapshot):
            return False
        if snapshot.fixture.fixture_id != self.__fixture.fixture_id:
            return False
        if snapshot == self.__first or snapshot == self.__second:
            return False
        if self.__first is None:
            self.__first = snapshot
            return True
        if self.__second is None:
            self.__second = snapshot
            return True
        return False

    def remove_snapshot(self, snapshot):
        if snapshot is None:
            return False
        if snapshot == self.__first:
            self.__first = None
            return True
        if snapshot == self.__second:
            self.__second = None
            return True
        return False

    def __matches(self, snapshot, bookmaker, timestamp):
        return (snapshot is not None
                and snapshot.bookmaker == bookmaker
                and snapshot.recorded_at <= timestamp)

    def latest_at(self, bookmaker, timestamp):
        latest = None
        if self.__matches(self.__first, bookmaker, timestamp):
            latest = self.__first
        if self.__matches(self.__second, bookmaker, timestamp):
            if latest is None or self.__second.recorded_at > latest.recorded_at:
                latest = self.__second
        return latest

    def price_change(self, bookmaker, outcome, start, end):
        """End price minus start price, using the latest records at each time."""
        if start > end:
            return None
        first = self.latest_at(bookmaker, start)
        last = self.latest_at(bookmaker, end)
        if first is None or last is None:
            return None
        first_quote = first.get_quote(outcome)
        last_quote = last.get_quote(outcome)
        if first_quote is None or last_quote is None:
            return None
        if first_quote.decimal_odds is None or last_quote.decimal_odds is None:
            return None
        return last_quote.decimal_odds - first_quote.decimal_odds

    def __str__(self):
        count = 0
        if self.__first is not None:
            count += 1
        if self.__second is not None:
            count += 1
        return f"History for {self.__fixture}: {count}/2 snapshots"
