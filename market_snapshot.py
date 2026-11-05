from odds_exceptions import UnknownOutcomeError
from odds_quote import OddsQuote


class MarketSnapshot:
    """Own three quotes recorded at a timezone-aware datetime."""

    def __init__(self, fixture, bookmaker, recorded_at, home, draw, away):
        self.__fixture = fixture
        self.__bookmaker = bookmaker
        self.__recorded_at = recorded_at
        self.__quotes = {
            "home": OddsQuote("home", home),
            "draw": OddsQuote("draw", draw),
            "away": OddsQuote("away", away),
        }

    def get_fixture(self):
        return self.__fixture

    fixture = property(get_fixture)

    def get_bookmaker(self):
        return self.__bookmaker

    bookmaker = property(get_bookmaker)

    def get_recorded_at(self):
        return self.__recorded_at

    recorded_at = property(get_recorded_at)

    @staticmethod
    def is_supported_outcome(outcome):
        """Check whether an outcome belongs to the home/draw/away market."""
        return outcome in ("home", "draw", "away")

    def get_quote(self, outcome):
        """Look up a quote, raising UnknownOutcomeError for an unsupported key."""
        if not self.is_supported_outcome(outcome):
            raise UnknownOutcomeError(outcome)
        return self.__quotes[outcome]

    def get_quotes(self):
        """Return a copy so callers cannot replace or remove the stored quotes."""
        return self.__quotes.copy()

    quotes = property(get_quotes)

    def is_complete(self):
        return all(quote.decimal_odds is not None
                   for quote in self.__quotes.values())

    def favourite_outcome(self):
        """Return the lowest-priced outcome, or None for an incomplete market.

        Ties use dictionary order: home, draw, then away.
        """
        if not self.is_complete():
            return None
        favourite = None
        lowest_odds = None
        for outcome, quote in self.__quotes.items():
            if lowest_odds is None or quote.decimal_odds < lowest_odds:
                favourite = outcome
                lowest_odds = quote.decimal_odds
        return favourite

    def calculate_overround(self):
        """Return the probability total above 1, e.g. 0.05 means 5%."""
        if not self.is_complete():
            return None
        return sum(quote.implied_probability()
                   for quote in self.__quotes.values()) - 1

    def __str__(self):
        quotes = ", ".join(str(quote) for quote in self.__quotes.values())
        return f"{self.__bookmaker}, {self.__recorded_at}: {quotes}"
