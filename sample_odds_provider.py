from market_snapshot import MarketSnapshot
from odds_provider import OddsProvider


class SampleOddsProvider(OddsProvider):
    """Create a fresh snapshot from one set of manually supplied sample prices."""

    def __init__(self, fixture, bookmaker, recorded_at, home, draw, away):
        super().__init__("Manually supplied sample odds")
        self.__fixture = fixture
        self.__bookmaker = bookmaker
        self.__recorded_at = recorded_at
        self.__home = home
        self.__draw = draw
        self.__away = away

    def load_snapshot(self):
        return MarketSnapshot(self.__fixture, self.__bookmaker, self.__recorded_at,
                              self.__home, self.__draw, self.__away)
