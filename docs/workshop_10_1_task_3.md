# Workshop 10-1: Task 3 - Raise Exceptions

The existing rule-enforcement methods now raise the exceptions defined in
Task 2. Successful operations retain their normal return values.

| Method | Invalid condition | Exception raised |
| --- | --- | --- |
| `OddsQuote.__init__()` | A supplied price is invalid, excluding intentional `None` | `InvalidDecimalOddsError` |
| `OddsComparator.set_maximum_quote_age()` | The limit is not a non-negative integer number of minutes | `InvalidQuoteAgeError` |
| `OddsHistory.add_snapshot()` | The snapshot belongs to another fixture | `FixtureMismatchError` |
| `OddsComparator.compare()` | The snapshots belong to different fixtures | `FixtureMismatchError` |
| `OddsHistory.add_snapshot()` | The same snapshot object is already stored | `DuplicateSnapshotError` |
| `OddsHistory.remove_snapshot()` | A supplied snapshot object is absent | `SnapshotNotFoundError` |
| `MarketSnapshot.get_quote()` | The outcome is unsupported | `UnknownOutcomeError` |
| `OddsHistory.price_change()` | The outcome is unsupported | `UnknownOutcomeError` |
| `OddsHistory.price_change()` | Start is later than end | `InvalidTimeRangeError` |

`OddsComparator` construction uses its property setter, so an invalid initial
limit also raises `InvalidQuoteAgeError`. Invalid prices encountered while
constructing a `MarketSnapshot`, including through `SampleOddsProvider`,
propagate `InvalidDecimalOddsError` to the caller. Comparison uses `get_quote()`,
so unsupported outcomes propagate `UnknownOutcomeError` as well.

`MarketSnapshot.is_supported_outcome()` is a shared Boolean check for the three
supported keys. History checks the key before looking for records, so an unknown
outcome is reported even when the history is empty. Price-change validation
checks the time interval first if both the interval and outcome are invalid.

## State protection and normal behaviour

- Odds validation occurs before quote fields are assigned. Invalid construction
  does not return a quote or containing snapshot.
- An invalid quote-age update raises before changing the existing limit.
- Fixture and duplicate checks occur before appending to history, and membership
  is checked before removing a snapshot. Failed updates preserve list order and
  contents.
- Lookups and calculations do not modify the stored quotes or snapshots.
- `None` still represents unavailable prices. Incomplete markets, missing history
  and comparisons with no eligible snapshots retain their ordinary results.
- Distinct snapshot objects and separate fixture objects with matching IDs remain
  acceptable. Equal timestamps remain valid for a price-change request.
- Inputs that are not `MarketSnapshot` objects retain the existing `False` or
  `None` results in history updates and comparison. These were not selected as
  custom exception cases in Task 1.

## Verification and remaining workshop tasks

A temporary, unsaved verification script caught 55 expected exceptions across the
seven error types. It checked message details, unchanged state after rejection,
and successful operations after the errors were caught. It also checked ordinary
missing-data results, eligibility exclusions, repeated prices, matching fixture
IDs and valid boundary values.

The existing pytest suite was run without modifying its tests: **54 passed,
10 failed and 4 had setup errors**. The failures and setup errors arise where
the old tests expect invalid operations to return `False` or `None`, or create
invalid objects as fixtures. The demonstration test also fails because `main.py`
still requests an unknown outcome without a handler.

This is the intermediate Task 3 state. Recovery within object-oriented behaviour
outside `main.py` is Task 4, updating the pytest suite to expect exceptions is
Task 5, and updating the demonstration is Task 6. No handlers, test edits or
demonstration edits have been added in this task.
