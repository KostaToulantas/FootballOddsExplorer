class Fixture:
    """A match with a timezone-aware datetime for kickoff."""

    def __init__(self, fixture_id, home_team, away_team, kickoff_time):
        self.__fixture_id = fixture_id
        self.__home_team = home_team
        self.__away_team = away_team
        self.__kickoff_time = kickoff_time

    def get_fixture_id(self):
        return self.__fixture_id

    fixture_id = property(get_fixture_id)

    def is_before_kickoff(self, timestamp):
        return timestamp < self.__kickoff_time

    def __str__(self):
        return f"{self.__home_team} vs {self.__away_team} (kickoff: {self.__kickoff_time})"
