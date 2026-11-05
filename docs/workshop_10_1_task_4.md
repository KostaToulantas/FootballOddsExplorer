# Workshop 10-1: Task 4 - Handle Exceptions

`OddsExplorer` in `odds_explorer.py` coordinates an existing `OddsHistory` and
`OddsComparator`. Its instance methods wrap operations that can raise the custom
exceptions, catch the expected types and print feedback containing the exception
message. All exception handlers are outside `main.py`.

| Application method | Expected exceptions handled | Result after a handled error |
| --- | --- | --- |
| `load_snapshot()` | `InvalidDecimalOddsError` from the provider's snapshot construction | `None`; no snapshot is returned or added to history |
| `get_quote()` | `UnknownOutcomeError` | `None`; the stored quotes are unchanged |
| `add_snapshot()` | `FixtureMismatchError`, `DuplicateSnapshotError` | `False`; history contents and order are unchanged |
| `remove_snapshot()` | `SnapshotNotFoundError` | `False`; history contents and order are unchanged |
| `compare()` | `FixtureMismatchError`, `UnknownOutcomeError` | `None`; both snapshots are unchanged |
| `set_maximum_quote_age()` | `InvalidQuoteAgeError` | `False`; the previous age limit remains in use |
| `price_change()` | `InvalidTimeRangeError`, `UnknownOutcomeError` | `None`; history and prices are unchanged |

Successful results pass through unchanged. A successful age-limit update returns
`True`. Handled errors explain the failed operation, for example:

```text
Quote lookup failed: Unknown outcome 'unknown': choose home, draw or away.
Snapshot not loaded: Invalid home odds 0.5: decimal odds must be a finite number greater than 1.
Quote age limit not changed: Invalid maximum quote age -1: use a non-negative integer number of minutes.
```

The domain classes retain their Task 3 exceptions. Callers wanting recovery use
`OddsExplorer`; later pytest tests can still observe the exceptions directly on
the domain methods. The application catches only the expected custom exception
types for each operation, so unrelated programming errors are not concealed.

## Existing demonstration

The existing operations in `main.py` now use the application methods for loading,
invalid outcome lookup, history updates, comparison, age-limit updates and price
changes. There are no `try` or `except` statements in `main.py`.

The old invalid-price example now attempts a provider load through `OddsExplorer`
and reports its rejection. A separate snapshot with an explicitly unavailable
home price (`None`) preserves the existing incomplete-market example. Rejected
prices are not silently converted to unavailable prices.

These changes restore the existing demonstration's ability to finish. Expanding
it with the remaining exceptional scenarios is reserved for Task 6.

## Verification

- `python main.py` completes successfully. It handles an unknown outcome, invalid
  odds and a duplicate snapshot, then continues through history queries, removal,
  collection protection and price comparisons.
- An unsaved verification script checked 30 handled-error cases covering all
  seven exception types. Each checked feedback, unchanged history and quotes,
  an unchanged quote-age limit and a subsequent successful comparison.
- Additional checks confirmed successful load, lookup, removal, re-addition,
  configuration and price-change operations. Removing an already removed
  snapshot produced feedback and left the remaining history intact.
- Ordinary unavailable prices and no-result queries remain valid and do not
  print error feedback. An unexpected provider `RuntimeError` still propagates.
- The existing pytest suite reports **55 passed, 9 failed and 4 setup errors**.
  The demonstration test now passes. The remaining failures and setup errors
  are the old domain tests that expect invalid operations to return `False` or
  `None`, or construct invalid objects as fixtures. Updating those tests to
  expect raised exceptions is Task 5; no pytest files were changed in Task 4.
