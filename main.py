from datetime import datetime, timezone

from bookmaker import Bookmaker
from fixture import Fixture
from odds_comparator import OddsComparator
from odds_history import OddsHistory
from odds_quote import OddsQuote
from sample_odds_provider import SampleOddsProvider


def show_best(comparator, first, second, outcome, as_of):
    best = comparator.compare(first, second, outcome, as_of)
    if best is None:
        print(f"{outcome}: no eligible comparison")
    else:
        print(f"Best {outcome}: {best.bookmaker}, {best.get_quote(outcome)}")


def main():
    print("Football Odds Explorer - foundation demonstration")
    print("Fictional prices and fixture. All dates and times are shown in UTC.\n")
    kickoff = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
    earlier_time = datetime(2026, 9, 25, 18, 50, tzinfo=timezone.utc)
    first_time = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 25, 19, 12, tzinfo=timezone.utc)
    comparison_time = datetime(2026, 9, 25, 19, 15, tzinfo=timezone.utc)
    before_second_time = datetime(2026, 9, 25, 19, 11, tzinfo=timezone.utc)
    fixture = Fixture("F001", "Liverpool", "Arsenal", kickoff)
    bookmaker_a = Bookmaker("A", "Sample Sports")
    bookmaker_b = Bookmaker("B", "Demo Markets")
    print(fixture)
    print("Same bookmaker ID:", bookmaker_a == Bookmaker("A", "Sample Sports"))

    earlier_provider = SampleOddsProvider(
        fixture, bookmaker_a, earlier_time, 2.10, 3.40, 3.60)
    first_provider = SampleOddsProvider(
        fixture, bookmaker_a, first_time, 2.20, 3.40, 3.50)
    second_provider = SampleOddsProvider(
        fixture, bookmaker_b, second_time, 2.30, 3.30, 3.40)
    earlier = earlier_provider.load_snapshot()
    first = first_provider.load_snapshot()
    second = second_provider.load_snapshot()
    print("\nSource:", first_provider)
    print(first)
    print(second)
    print(
        f"Home implied probability: {first.get_quote('home').implied_probability():.2%}")
    print(f"Market overround: {first.calculate_overround():.2%}")

    history = OddsHistory(fixture)
    print("\nAdd earlier snapshot:", history.add_snapshot(earlier))
    print("Add later snapshot:", history.add_snapshot(first))
    print("Reject duplicate:", history.add_snapshot(first))
    print("Reject third snapshot (foundation capacity):",
          history.add_snapshot(second))
    print(history)
    print(f"Latest at {comparison_time}:",
          history.latest_at(bookmaker_a, comparison_time))
    print(
        f"Home price change: {history.price_change(bookmaker_a, 'home', earlier_time, comparison_time):+.2f}")
    print("Remove earlier snapshot:", history.remove_snapshot(earlier))
    print(history)

    comparator = OddsComparator(10)
    print(f"\nComparison at {comparison_time}:")
    show_best(comparator, first, second, "home", comparison_time)
    show_best(comparator, first, second, "draw", comparison_time)
    show_best(comparator, first, second, "away", comparison_time)
    print("At kickoff:", comparator.compare(first, second, "home", kickoff))
    print("Future quote eligible:", comparator.is_eligible(
        second, before_second_time))
    comparator.maximum_quote_age = 2
    print("After reducing maximum quote age to 2 minutes:")
    show_best(comparator, first, second, "home", comparison_time)
    print("Invalid odds:", OddsQuote("home", 0.5))


if __name__ == "__main__":
    main()
