class Bookmaker:
    """Identify a source of odds, even across separate objects."""

    def __init__(self, bookmaker_id, name):
        self.__bookmaker_id = bookmaker_id
        self.__name = name

    def __eq__(self, other):
        if not isinstance(other, Bookmaker):
            return False
        return self.__bookmaker_id == other.__bookmaker_id

    def __str__(self):
        return self.__name
