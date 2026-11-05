"""Domain exceptions for invalid Football Odds Explorer operations."""


class OddsExplorerError(Exception):
    """Shared parent for errors specific to Football Odds Explorer."""


class InvalidDecimalOddsError(OddsExplorerError):
    """A supplied decimal price breaks the odds rule."""

    def __init__(self, outcome, value):
        super().__init__(
            f"Invalid {outcome} odds {value!r}: decimal odds must be a finite "
            "number greater than 1."
        )


class InvalidQuoteAgeError(OddsExplorerError):
    """A requested quote age limit is not a non-negative integer."""

    def __init__(self, value):
        super().__init__(
            f"Invalid maximum quote age {value!r}: use a non-negative integer "
            "number of minutes."
        )


class FixtureMismatchError(OddsExplorerError):
    """A snapshot belongs to a different fixture from the one required."""

    def __init__(self, operation, expected_fixture_id, actual_fixture_id):
        super().__init__(
            f"Cannot {operation}: snapshot fixture {actual_fixture_id} "
            f"does not match fixture {expected_fixture_id}."
        )


class DuplicateSnapshotError(OddsExplorerError):
    """The same snapshot object is already stored in the history."""

    def __init__(self, fixture_id, bookmaker, recorded_at):
        super().__init__(
            f"Snapshot for fixture {fixture_id} from {bookmaker} "
            f"at {recorded_at} is already stored."
        )


class SnapshotNotFoundError(OddsExplorerError):
    """A snapshot requested for removal is absent from the history."""

    def __init__(self, fixture_id, bookmaker, recorded_at):
        super().__init__(
            f"Cannot remove {bookmaker} snapshot at {recorded_at}: "
            f"it is not stored in history for fixture {fixture_id}."
        )


class UnknownOutcomeError(OddsExplorerError):
    """The requested outcome is not part of the home/draw/away market."""

    def __init__(self, outcome):
        super().__init__(
            f"Unknown outcome {outcome!r}: choose home, draw or away."
        )


class InvalidTimeRangeError(OddsExplorerError):
    """A price-change interval starts after it ends."""

    def __init__(self, start, end):
        super().__init__(
            f"Cannot calculate price change from {start} to {end}: "
            "start must not be after end."
        )
