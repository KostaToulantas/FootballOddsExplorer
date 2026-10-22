from market_snapshot import MarketSnapshot


class OddsHistory:
    """Manage a fixture's snapshots in insertion order, without a fixed capacity."""

    def __init__(self, fixture):
        self.__fixture = fixture
        self.__snapshots = []

    def get_snapshots(self):
        """Return a copy so callers cannot add or remove stored snapshots directly."""
        return self.__snapshots.copy()

    snapshots = property(get_snapshots)

    def has_snapshot(self, snapshot):
        """Check whether this snapshot object is already stored."""
        return snapshot in self.__snapshots

    def add_snapshot(self, snapshot):
        if not isinstance(snapshot, MarketSnapshot):
            return False
        if snapshot.fixture.fixture_id != self.__fixture.fixture_id:
            return False
        if self.has_snapshot(snapshot):
            return False
        self.__snapshots.append(snapshot)
        return True

    def remove_snapshot(self, snapshot):
        if not self.has_snapshot(snapshot):
            return False
        self.__snapshots.remove(snapshot)
        return True

    def filter_by_bookmaker(self, bookmaker):
        """Find a bookmaker's records in insertion order, returning a new list."""
        return [
            snapshot for snapshot in self.__snapshots
            if snapshot.bookmaker == bookmaker
        ]

    def snapshots_at(self, bookmaker, timestamp):
        """Filter records for a bookmaker, excluding records after the requested time."""
        return [
            snapshot for snapshot in self.filter_by_bookmaker(bookmaker)
            if snapshot.recorded_at <= timestamp
        ]

    def latest_at(self, bookmaker, timestamp):
        latest = None
        for snapshot in self.snapshots_at(bookmaker, timestamp):
            if latest is None or snapshot.recorded_at > latest.recorded_at:
                latest = snapshot
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
        return f"History for {self.__fixture}: {len(self.__snapshots)} snapshots"
