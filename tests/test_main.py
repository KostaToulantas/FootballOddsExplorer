"""Check that the complete demonstration runs successfully."""

from main import main


class TestMain:
    def test_demonstration_completes(self):
        # Detailed class and interaction tests check the individual results.
        assert main() is None
