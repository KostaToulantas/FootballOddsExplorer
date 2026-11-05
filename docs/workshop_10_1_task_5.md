# Workshop 10-1: Task 5 - Test Raised Exceptions

The pytest suite now checks the exceptions introduced in Tasks 2 and 3 and the
recovery added in Task 4. Only tests and this documentation changed in Task 5.

## Direct exception tests

`pytest.raises()` surrounds the domain operation that is expected to fail, rather
than object creation in a fixture. Fixtures supply usable objects; invalid
construction happens inside the test's `pytest.raises()` block.

| Test module | Exception behaviour checked |
| --- | --- |
| `test_odds_quote.py` | Invalid numeric and non-numeric prices raise `InvalidDecimalOddsError`, with the rejected value, outcome and price rule in the message |
| `test_market_snapshot.py` | Invalid prices reject construction for each outcome; unknown keys raise `UnknownOutcomeError` without changing stored quotes |
| `test_odds_comparator.py` | Invalid initial limits and updates raise `InvalidQuoteAgeError`; updates preserve the previous limit; mismatched fixtures and unknown outcomes raise their specific exceptions |
| `test_odds_history.py` | Duplicate additions, mismatched fixtures, missing removals, reversed intervals and unknown outcomes raise the expected exceptions and preserve relevant state |
| `test_sample_odds_provider.py` | Invalid prices for home, draw and away propagate `InvalidDecimalOddsError` when loading a snapshot |
| `test_object_interactions.py` | Rejected operations preserve history order, snapshot references, quotes and subsequent comparisons across collaborating objects |

Tests check useful message details such as both fixture IDs, bookmaker names,
timezone-aware recording times, rejected values, supported outcomes and interval
ordering. State checks use public properties and methods.

The old invalid-object fixtures were removed or corrected. `None` prices remain
valid unavailable data, so the incomplete-market fixtures now use `None` rather
than invalid numeric prices. Existing successful, boundary and ordinary
no-result behaviour remains covered.

## Recovery tests

The new `test_odds_explorer.py` uses realistic fixtures, bookmakers, snapshots,
history and a comparator. These tests call the recovery methods normally and
check their `False` or `None` results, rather than expecting handled exceptions
to escape.

`capsys` checks the printed feedback. The tests also verify that failed updates
preserve data and configuration and that valid operations work afterward.
Unavailable prices and ordinary no-result queries produce no error feedback.
An unexpected provider error is checked separately to ensure the handlers do not
hide unrelated failures.

## Results

Run from the `FootballOddsExplorer` directory:

```text
python -m coverage run --branch --source=. --omit="tests/*" -m pytest -q -p no:cacheprovider --tb=short
python -m coverage report -m
```

- **129 tests passed**, with no failures or setup errors.
- Coverage reports **99% overall** with branch measurement enabled.
- All domain modules, including `odds_exceptions.py` and `odds_explorer.py`, report
  **100%** except the abstract `odds_provider.py` module. The only uncovered
  statements are its abstract method's `pass` and the direct-entry `main()` call
  under `if __name__ == "__main__"`. The demonstration itself runs through its
  existing pytest test.

Task 6 demonstration expansion and Task 8 final submission review remain for
later commits.
