from odds_quote import OddsQuote


class MarketSnapshot:
    """Own three quotes recorded at a timezone-aware datetime."""

    def __init__(self, fixture, bookmaker, recorded_at, home, draw, away):
        self.__fixture = fixture
        self.__bookmaker = bookmaker
        self.__recorded_at = recorded_at
        self.__home = OddsQuote("home", home)
        self.__draw = OddsQuote("draw", draw)
        self.__away = OddsQuote("away", away)

    def get_fixture(self):
        return self.__fixture

    fixture = property(get_fixture)

    def get_bookmaker(self):
        return self.__bookmaker

    bookmaker = property(get_bookmaker)

    def get_recorded_at(self):
        return self.__recorded_at

    recorded_at = property(get_recorded_at)

    def get_quote(self, outcome):
        if outcome == "home":
            return self.__home
        if outcome == "draw":
            return self.__draw
        if outcome == "away":
            return self.__away
        return None

    def is_complete(self):
        return (self.__home.decimal_odds is not None
                and self.__draw.decimal_odds is not None
                and self.__away.decimal_odds is not None)

    def calculate_overround(self):
        """Return the probability total above 1, e.g. 0.05 means 5%."""
        if not self.is_complete():
            return None
        return (self.__home.implied_probability()
                + self.__draw.implied_probability()
                + self.__away.implied_probability() - 1)

    def __str__(self):
        return (f"{self.__bookmaker}, {self.__recorded_at}: "
                f"{self.__home}, {self.__draw}, {self.__away}")
