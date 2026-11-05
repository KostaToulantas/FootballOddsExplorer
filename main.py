from datetime import datetime, timezone

from bookmaker import Bookmaker
from fixture import Fixture
from market_snapshot import MarketSnapshot
from odds_comparator import OddsComparator
from odds_explorer import OddsExplorer
from odds_history import OddsHistory
from odds_provider import OddsProvider
from sample_odds_provider import SampleOddsProvider


def show_best(explorer, first, second, outcome, as_of):
    best = explorer.compare(first, second, outcome, as_of)
    if best is None:
        print(f"{outcome}: no eligible comparison")
    else:
        print(f"Best {outcome}: {best.bookmaker}, {best.get_quote(outcome)}")


def main():
    print("Football Odds Explorer - exception handling demonstration")
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
    history = OddsHistory(fixture)
    comparator = OddsComparator(10)
    explorer = OddsExplorer(history, comparator)
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

    print("\nABSTRACTION AND INHERITANCE: load through the provider interface")
    print("Sample provider inherits OddsProvider:",
          isinstance(first_provider, OddsProvider))
    print("Source:", first_provider)
    earlier = explorer.load_snapshot(earlier_provider)
    first = explorer.load_snapshot(first_provider)
    second = explorer.load_snapshot(second_provider)
    third = explorer.load_snapshot(third_provider)
    print("\nDICTIONARY: store quote objects under outcome names")
    print("Loading each snapshot populates its dictionary with three quotes.")
    for snapshot in [first, second]:
        print(f"\n{snapshot.bookmaker}: {len(snapshot.quotes)} outcome keys")
        for outcome, quote in snapshot.quotes.items():
            print(f"  Key '{outcome}' -> quote with odds {quote.decimal_odds:.2f}")
        favourite = snapshot.favourite_outcome()
        print("Favourite outcome:", snapshot.get_quote(favourite))
        print(f"Market overround: {snapshot.calculate_overround():.2%}")

    print("\nLook up the home key:", first.get_quote("home"))
    print("Look up an unknown key:", explorer.get_quote(first, "unknown"))
    print(
        f"Home implied probability: {first.get_quote('home').implied_probability():.2%}")
    invalid_provider = SampleOddsProvider(
        fixture, bookmaker_a, first_time, 0.5, 3.40, 3.50)
    invalid_snapshot = explorer.load_snapshot(invalid_provider)
    print("Invalid snapshot was loaded:", invalid_snapshot is not None)
    corrected_provider = SampleOddsProvider(
        fixture, bookmaker_a, first_time, 2.20, 3.40, 3.50)
    corrected_snapshot = explorer.load_snapshot(corrected_provider)
    print("Corrected snapshot loaded successfully:", corrected_snapshot.is_complete())
    incomplete = MarketSnapshot(
        fixture, bookmaker_a, first_time, None, 3.40, 3.50)
    print("Unavailable home quote:", incomplete.get_quote("home"))
    print("Market with unavailable home odds is complete:", incomplete.is_complete())
    print("Favourite in that incomplete market:", incomplete.favourite_outcome())

    print("\nLIST: store snapshot objects in insertion order")
    for snapshot in [earlier, first, second, third]:
        added = explorer.add_snapshot(snapshot)
        print(f"Add {snapshot.bookmaker} at {snapshot.recorded_at}: {added}")
    original_history = history.snapshots
    print("Add the same snapshot object again (rejected):",
          explorer.add_snapshot(first))
    other_fixture = Fixture("F002", "Chelsea", "Everton", kickoff)
    other_snapshot = MarketSnapshot(
        other_fixture, bookmaker_b, first_time, 9.00, 3.40, 3.50)
    print("Add a snapshot for another fixture (rejected):",
          explorer.add_snapshot(other_snapshot))
    print("History unchanged after rejected additions:",
          history.snapshots == original_history)
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
    original_history = history.snapshots
    print("Price change with a reversed interval (rejected):",
          explorer.price_change(
              bookmaker_a, "home", comparison_time, earlier_time))
    print("History unchanged after rejected price change:",
          history.snapshots == original_history)
    print(
        f"Home price change: {explorer.price_change(bookmaker_a, 'home', earlier_time, comparison_time):+.2f}")
    print("Remove earlier snapshot:", explorer.remove_snapshot(earlier))
    print("Earlier snapshot is still stored:", history.has_snapshot(earlier))
    remaining_history = history.snapshots
    print("Remove the earlier snapshot again (rejected):",
          explorer.remove_snapshot(earlier))
    print("History unchanged after rejected removal:",
          history.snapshots == remaining_history)
    print(history)

    print("\nENCAPSULATION: viewing copies protects the stored collections")
    history_copy = history.snapshots
    history_copy.clear()
    quotes_copy = first.quotes
    quotes_copy.clear()
    print("After clearing an external history copy:", history)
    print("After clearing an external quotes copy, market complete:",
          first.is_complete())

    print(f"\nCOMPARISON: best available odds at {comparison_time}")
    original_quotes = (first.quotes, other_snapshot.quotes)
    print("Compare snapshots for different fixtures (rejected):",
          explorer.compare(first, other_snapshot, "home", comparison_time))
    print("Quotes unchanged after rejected comparison:",
          (first.quotes, other_snapshot.quotes) == original_quotes)
    show_best(explorer, first, second, "home", comparison_time)
    show_best(explorer, first, second, "draw", comparison_time)
    show_best(explorer, first, second, "away", comparison_time)
    print("At kickoff:", explorer.compare(first, second, "home", kickoff))
    print("Future quote eligible:", comparator.is_eligible(
        second, before_second_time))
    print("Set maximum quote age to -1 minutes (rejected):",
          explorer.set_maximum_quote_age(-1))
    print("Maximum quote age after rejection:", comparator.maximum_quote_age,
          "minutes")
    show_best(explorer, first, second, "home", comparison_time)
    explorer.set_maximum_quote_age(2)
    print("After reducing maximum quote age to 2 minutes:")
    show_best(explorer, first, second, "home", comparison_time)

    print("\nCONTINUING AFTER HANDLED EXCEPTIONS")
    print("Restore maximum quote age to 10 minutes:",
          explorer.set_maximum_quote_age(10))
    print("History still contains the three retained snapshots:",
          history.snapshots == [first, second, third])
    latest_a = history.latest_at(bookmaker_a, comparison_time)
    latest_b = history.latest_at(bookmaker_b, comparison_time)
    show_best(explorer, latest_a, latest_b, "home", comparison_time)


if __name__ == "__main__":
    main()
