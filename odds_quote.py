class OddsQuote:
    """One recorded price. None marks an invalid price, without exceptions."""

    def __init__(self, outcome, decimal_odds):
        self.__outcome = outcome
        self.__decimal_odds = None
        if self.validate_odds(decimal_odds):
            self.__decimal_odds = decimal_odds

    def get_decimal_odds(self):
        return self.__decimal_odds

    decimal_odds = property(get_decimal_odds)

    def validate_odds(self, value):
        if isinstance(value, bool):
            return False
        if not isinstance(value, int) and not isinstance(value, float):
            return False
        return value > 1 and value < float("inf")

    def implied_probability(self):
        if self.__decimal_odds is None:
            return None
        return 1 / self.__decimal_odds

    def __str__(self):
        if self.__decimal_odds is None:
            return f"{self.__outcome}: unavailable"
        return f"{self.__outcome}: {self.__decimal_odds:.2f}"
