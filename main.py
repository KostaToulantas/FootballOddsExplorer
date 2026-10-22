from datetime import datetime, timezone

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_comparator import OddsComparator
from odds_history import OddsHistory
from sample_odds_provider import SampleOddsProvider


def show_best(comparator, first, second, outcome, as_of):
    best = comparator.compare(first, second, outcome, as_of)
    if best is None:
        print(f"{outcome}: no eligible comparison")
    else:
        print(f"Best {outcome}: {best.bookmaker}, {best.get_quote(outcome)}")


def main():
    print("Football Odds Explorer - data structures demonstration")
    print("Fictional prices and fixture. All dates and times are shown in UTC.\n")
    kickoff = datetime(2026, 9, 25, 19, 30, tzinfo=timezone.utc)
    earlier_time = datetime(2026, 9, 25, 18, 50, tzinfo=timezone.utc)
    first_time = datetime(2026, 9, 25, 19, 10, tzinfo=timezone.utc)
    second_time = datetime(2026, 9, 25, 19, 12, tzinfo=timezone.utc)
    third_time = datetime(2026, 9, 25, 19, 20, tzinfo=timezone.utc)
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
    third_provider = SampleOddsProvider(
        fixture, bookmaker_a, third_time, 2.20, 3.30, 3.60)

    print("\nDICTIONARY: store quote objects under outcome names")
    print("Loading each snapshot populates its dictionary with three quotes.")
    earlier = earlier_provider.load_snapshot()
    first = first_provider.load_snapshot()
    second = second_provider.load_snapshot()
    third = third_provider.load_snapshot()
    print("Source:", first_provider)
    for snapshot in [first, second]:
        print(f"\n{snapshot.bookmaker}: {len(snapshot.quotes)} outcome keys")
        for outcome, quote in snapshot.quotes.items():
            print(f"  Key '{outcome}' -> quote with odds {quote.decimal_odds:.2f}")
        favourite = snapshot.favourite_outcome()
        print("Favourite outcome:", snapshot.get_quote(favourite))
        print(f"Market overround: {snapshot.calculate_overround():.2%}")

    print("\nLook up the home key:", first.get_quote("home"))
    print("Look up an unknown key:", first.get_quote("unknown"))
    print(
        f"Home implied probability: {first.get_quote('home').implied_probability():.2%}")
    incomplete = MarketSnapshot(
        fixture, bookmaker_a, first_time, 0.5, 3.40, 3.50)
    print("Invalid home quote:", incomplete.get_quote("home"))
    print("Market with invalid home odds is complete:", incomplete.is_complete())
    print("Favourite in that incomplete market:", incomplete.favourite_outcome())

    print("\nLIST: store snapshot objects in insertion order")
    history = OddsHistory(fixture)
    for snapshot in [earlier, first, second, third]:
        added = history.add_snapshot(snapshot)
        print(f"Add {snapshot.bookmaker} at {snapshot.recorded_at}: {added}")
    print("Add the same snapshot object again (rejected):",
          history.add_snapshot(first))
    print(history)
    print("All stored snapshots, in insertion order:")
    for snapshot in history.snapshots:
        print(snapshot)
    print("The 19:10 and 19:20 records both keep home odds of 2.20.")
    print("Earlier snapshot is stored:", history.has_snapshot(earlier))
    print(f"All snapshots for {bookmaker_a}:")
    for snapshot in history.filter_by_bookmaker(bookmaker_a):
        print(" ", snapshot)
    print(f"Snapshots for {bookmaker_a} recorded by {comparison_time}:")
    for snapshot in history.snapshots_at(bookmaker_a, comparison_time):
        print(" ", snapshot)
    print(f"Latest at {comparison_time}:",
          history.latest_at(bookmaker_a, comparison_time))
    print("The 19:20 record is excluded because it is after the requested time.")
    print(
        f"Home price change: {history.price_change(bookmaker_a, 'home', earlier_time, comparison_time):+.2f}")
    print("Remove earlier snapshot:", history.remove_snapshot(earlier))
    print("Earlier snapshot is still stored:", history.has_snapshot(earlier))
    print(history)

    print("\nENCAPSULATION: viewing copies protects the stored collections")
    history_copy = history.snapshots
    history_copy.clear()
    quotes_copy = first.quotes
    quotes_copy.clear()
    print("After clearing an external history copy:", history)
    print("After clearing an external quotes copy, market complete:",
          first.is_complete())

    comparator = OddsComparator(10)
    print(f"\nCOMPARISON: best available odds at {comparison_time}")
    show_best(comparator, first, second, "home", comparison_time)
    show_best(comparator, first, second, "draw", comparison_time)
    show_best(comparator, first, second, "away", comparison_time)
    print("At kickoff:", comparator.compare(first, second, "home", kickoff))
    print("Future quote eligible:", comparator.is_eligible(
        second, before_second_time))
    comparator.maximum_quote_age = 2
    print("After reducing maximum quote age to 2 minutes:")
    show_best(comparator, first, second, "home", comparison_time)


if __name__ == "__main__":
    main()
