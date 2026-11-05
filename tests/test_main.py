"""Check that the demonstration handles domain errors and continues normally."""

from main import main


class TestMain:
    def test_demonstration_completes_and_recovers(self, capsys):
        assert main() is None
        output = capsys.readouterr().out

        # All seven exception types must reach their application handlers.
        for feedback in [
            "Invalid home odds 0.5",
            "Unknown outcome 'unknown'",
            "is already stored",
            "snapshot fixture F002 does not match fixture F001",
            "it is not stored in history for fixture F001",
            "Invalid maximum quote age -1",
            "start must not be after end",
        ]:
            assert feedback in output

        for confirmation in [
            "Sample provider inherits OddsProvider: True",
            "Corrected snapshot loaded successfully: True",
            "History unchanged after rejected additions: True",
            "History unchanged after rejected price change: True",
            "History unchanged after rejected removal: True",
            "Quotes unchanged after rejected comparison: True",
            "Maximum quote age after rejection: 10 minutes",
            "Market with unavailable home odds is complete: False",
        ]:
            assert confirmation in output

        # A final normal operation must still succeed after the handled errors.
        final_section = output.split("CONTINUING AFTER HANDLED EXCEPTIONS", 1)[1]
        assert "Restore maximum quote age to 10 minutes: True" in final_section
        assert "History still contains the three retained snapshots: True" in final_section
        assert "Best home: Demo Markets, home: 2.30" in final_section
