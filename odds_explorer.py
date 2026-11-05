"""Application behaviour that recovers from expected football odds errors."""

from odds_exceptions import (
    DuplicateSnapshotError,
    FixtureMismatchError,
    InvalidDecimalOddsError,
    InvalidQuoteAgeError,
    InvalidTimeRangeError,
    SnapshotNotFoundError,
    UnknownOutcomeError,
)


class OddsExplorer:
    """Coordinate a history and comparator, reporting rejected user operations.

    Domain objects still raise exceptions when used directly. These application
    methods catch the errors a user can recover from and return False or None
    after printing the reason. Successful results pass through unchanged.
    """

    def __init__(self, history, comparator):
        self.__history = history
        self.__comparator = comparator

    def load_snapshot(self, provider):
        """Load a provider's snapshot, returning None if a supplied price is invalid."""
        try:
            return provider.load_snapshot()
        except InvalidDecimalOddsError as error:
            print(f"Snapshot not loaded: {error}")
            return None

    def get_quote(self, snapshot, outcome):
        """Look up an outcome, returning None if the outcome is unsupported."""
        try:
            return snapshot.get_quote(outcome)
        except UnknownOutcomeError as error:
            print(f"Quote lookup failed: {error}")
            return None

    def add_snapshot(self, snapshot):
        """Add a record, returning False if its fixture or stored state prevents it."""
        try:
            return self.__history.add_snapshot(snapshot)
        except (FixtureMismatchError, DuplicateSnapshotError) as error:
            print(f"Snapshot not added: {error}")
            return False

    def remove_snapshot(self, snapshot):
        """Remove a record, returning False if it is absent from this history."""
        try:
            return self.__history.remove_snapshot(snapshot)
        except SnapshotNotFoundError as error:
            print(f"Snapshot not removed: {error}")
            return False

    def compare(self, first, second, outcome, as_of):
        """Compare prices, returning None if the fixtures or outcome are invalid."""
        try:
            return self.__comparator.compare(first, second, outcome, as_of)
        except (FixtureMismatchError, UnknownOutcomeError) as error:
            print(f"Comparison failed: {error}")
            return None

    def set_maximum_quote_age(self, value):
        """Apply an age limit, returning False and keeping the old limit on failure."""
        try:
            self.__comparator.maximum_quote_age = value
        except InvalidQuoteAgeError as error:
            print(f"Quote age limit not changed: {error}")
            return False
        return True

    def price_change(self, bookmaker, outcome, start, end):
        """Calculate a price change, returning None for an invalid interval or key."""
        try:
            return self.__history.price_change(bookmaker, outcome, start, end)
        except (InvalidTimeRangeError, UnknownOutcomeError) as error:
            print(f"Price change failed: {error}")
            return None
