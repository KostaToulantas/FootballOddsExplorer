# Workshop 10-1: Task 1 - Identify Exceptional Situations

## Review of Football Odds Explorer

Football Odds Explorer creates home/draw/away market snapshots, stores them in a
fixture's history, compares eligible prices and calculates price changes. The
following situations were identified by reviewing the existing classes and tests.
They are proposed exception cases for the later workshop tasks; this task does
not change the program's behaviour or introduce exception classes.

## Selected exceptional situations

### 1. Supplying invalid decimal odds

- **Operation:** `OddsQuote.__init__()`, using the rule checked by
  `validate_odds()`.
- **Cause:** A supplied price is not a finite number greater than 1. Examples
  include `0.5`, `1`, `"2.20"`, `True`, infinity and NaN.
- **Current behaviour:** The quote is created with `decimal_odds` set to `None`,
  so an invalid supplied price becomes indistinguishable from unavailable odds.
- **Why an exception helps:** The supplied price breaks a betting-price rule.
  Reporting the failure lets the caller correct the input instead of silently
  creating an unavailable quote.
- **Useful information:** The outcome, rejected value and required rule. Example:
  `Invalid home odds 0.5: decimal odds must be a finite number greater than 1.`
- **State requirement:** Reject the invalid supplied price before a usable quote
  or containing snapshot is returned. Existing snapshots must remain unchanged.
  Keep `None` as an intentional unavailable price so incomplete markets remain
  representable.

### 2. Setting an invalid maximum quote age

- **Operation:** `OddsComparator.set_maximum_quote_age()`, also called during
  construction.
- **Cause:** The limit is negative, fractional, Boolean or non-numeric, such as
  `-1`, `2.5`, `True` or `"10"`. The rule requires a non-negative integer in minutes.
- **Current behaviour:** An invalid update is ignored; an invalid initial value
  leaves the limit at zero.
- **Why an exception helps:** Silent rejection can make users believe their
  requested freshness limit was applied, changing how they interpret comparisons.
- **Useful information:** The rejected value, units and accepted range. Example:
  `Invalid maximum quote age -1: use a non-negative integer number of minutes.`
- **State requirement:** A failed update must preserve the previous limit; invalid
  construction must not return a comparator with an unintended default limit.

### 3. Using a snapshot from a different fixture

- **Operations:** `OddsHistory.add_snapshot()` and `OddsComparator.compare()`.
- **Cause:** A snapshot's fixture ID differs from the history's fixture ID, or the
  two snapshots being compared have different fixture IDs. For example, adding
  Chelsea vs Everton (`F002`) to Liverpool vs Arsenal's history (`F001`).
- **Current behaviour:** Addition returns `False`; comparison returns `None`.
- **Why an exception helps:** The snapshot cannot participate in the requested
  operation because prices for different matches are not interchangeable. This
  is different from a valid comparison finding no eligible prices.
- **Useful information:** The operation and both fixture IDs, with team names
  where available. Example:
  `Cannot add snapshot for fixture F002 to history for fixture F001.`
- **State requirement:** Check fixture IDs before appending. Rejection must leave
  the history's contents and order unchanged. Comparison must change neither
  snapshot. Separate fixture objects with the same ID should still be accepted.

### 4. Adding the same snapshot object twice

- **Operation:** `OddsHistory.add_snapshot()`.
- **Cause:** The exact snapshot object is already in that history.
- **Current behaviour:** Returns `False` without adding another entry.
- **Why an exception helps:** The add operation cannot occur in the history's
  current state. Feedback should distinguish a duplicate from a fixture mismatch.
- **Useful information:** The fixture ID, bookmaker and recording time. Example:
  `Snapshot for F001 from Sample Sports at 2026-09-25 19:10 UTC is already stored.`
- **State requirement:** Preserve the list's contents and order. Distinct snapshot
  objects, including records with repeated prices, remain valid additions under
  the existing identity-based duplicate rule.

### 5. Removing a snapshot that is not stored

- **Operation:** `OddsHistory.remove_snapshot()`.
- **Cause:** The requested snapshot object is absent, including a snapshot already
  removed or a separate object containing the same data.
- **Current behaviour:** Returns `False`.
- **Why an exception helps:** A specific removal request cannot be completed
  because its target does not exist in this history. A membership query can still
  use the ordinary Boolean result from `has_snapshot()`.
- **Useful information:** The history's fixture ID and the requested snapshot's
  bookmaker and recording time. Example:
  `Cannot remove Sample Sports snapshot at 2026-09-25 19:10 UTC: it is not stored in history F001.`
- **State requirement:** Check membership before removing anything. All stored
  snapshots and their order must remain unchanged after failure.

### 6. Requesting an unsupported market outcome

- **Operation:** `MarketSnapshot.get_quote()`, also used by
  `OddsComparator.compare()` and `OddsHistory.price_change()`.
- **Cause:** The requested outcome is not one of `home`, `draw` or `away`, such as
  `"unknown"` or `"HOME"`.
- **Current behaviour:** Quote lookup returns `None`; comparison and price-change
  requests also return `None` for an unknown outcome.
- **Why an exception helps:** This market has no quote with that outcome key.
  Explicit feedback separates an invalid request from unavailable prices for a
  supported outcome.
- **Useful information:** The rejected outcome and supported keys. Example:
  `Unknown outcome 'HOME': choose home, draw or away.`
- **State requirement:** Lookup and any failed calculation must leave the quote
  dictionary, snapshots and history unchanged.

### 7. Calculating a price change over a reversed time interval

- **Operation:** `OddsHistory.price_change()`.
- **Cause:** `start` is later than `end`, for example requesting a change from
  19:20 back to 19:10 on the same day.
- **Current behaviour:** Returns `None`.
- **Why an exception helps:** The interval breaks the calculation's chronological
  rule. This needs different feedback from a valid interval with no recorded odds.
- **Useful information:** The start and end timestamps, including timezones, and
  the ordering rule. Example:
  `Cannot calculate price change from 2026-09-25 19:20 UTC to 2026-09-25 19:10 UTC: start must not be after end.`
- **State requirement:** Validate the interval before calculating. History and
  prices must remain unchanged. Equal start and end times remain valid.

## Ordinary outcomes that should keep normal return values

- `validate_odds()`, `has_snapshot()`, `is_complete()` and `is_eligible()` answer
  questions, so their expected negative answers should remain `False`.
- A bookmaker filter finding no records should return an empty list;
  `latest_at()` finding no record at or before a valid query time should return
  `None`.
- An explicitly unavailable price (`None`) should remain representable. An
  incomplete market can still report no favourite or overround, and a price
  change with unavailable endpoint prices can still return `None`.
- Stale prices, future records relative to the comparison time and a match that
  has reached kickoff are normal eligibility exclusions. A valid comparison
  with no eligible snapshots should continue to return `None`.
- A valid price-change request with insufficient history should return `None`.
  Equal prices should produce a change of zero, and tied comparison prices
  should retain the existing first-snapshot rule.

## Boundary for the later tasks

The selected cases describe invalid operations, rather than ordinary unsuccessful
searches or eligibility decisions. Later tasks will define and raise the custom
exceptions and catch them within object-oriented application behaviour outside
`main.py`. Those tasks will also verify useful feedback, unchanged state after a
failure and successful operations after recovery. No exception implementation,
handling, demonstration or test changes are part of Task 1.
