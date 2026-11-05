# Workshop 10-1: Task 6 - Demonstrate the Updated Creative Piece

Run from the `FootballOddsExplorer` directory:

```text
python main.py
```

The demonstration uses fictional fixtures and prices with timezone-aware UTC
timestamps. It shows successful operations, all seven custom exception types,
feedback from the application handlers and continued use after recovery.

## Exceptional situations and recovery

| Situation demonstrated | Handled feedback | State or subsequent successful behaviour shown |
| --- | --- | --- |
| Look up `unknown` | `UnknownOutcomeError` explains the supported outcome keys | The existing home quote still supplies its implied probability |
| Load home odds of `0.5` | `InvalidDecimalOddsError` explains the decimal price rule | No invalid snapshot is returned; a corrected provider loads a complete snapshot |
| Add the same snapshot twice | `DuplicateSnapshotError` identifies the stored record | History contents and insertion order stay unchanged |
| Add or compare a snapshot for `F002` against `F001` | `FixtureMismatchError` identifies both fixture IDs and the operation | History and quotes stay unchanged; valid comparisons still select the best odds |
| Calculate a change from 19:15 back to 18:50 | `InvalidTimeRangeError` reports the reversed timestamps | History stays unchanged; the valid interval produces a home price change of `+0.10` |
| Remove the already removed earlier snapshot | `SnapshotNotFoundError` identifies the absent record | The three remaining snapshots stay in order and remain available for queries |
| Set the maximum quote age to `-1` | `InvalidQuoteAgeError` explains the permitted age limit | The previous 10-minute limit remains active and another valid comparison succeeds |

The final section restores the age limit to 10 minutes, confirms the three
retained snapshots, retrieves the latest records from history and selects
`Demo Markets` with home odds of `2.30`. This operation occurs after all the
handled exception scenarios.

All exception handling remains in `OddsExplorer`. `main.py` calls its recovery
methods and contains no `try` or `except` statements.

## Existing Project 3 behaviour retained

- **Abstraction and inheritance:** The demonstration identifies
  `SampleOddsProvider` as an `OddsProvider` and loads snapshots through the common
  provider interface. The inherited source description is also displayed.
- **Dictionary:** Each snapshot owns the home, draw and away quotes. The
  demonstration iterates the keys, retrieves quotes and calculates favourites,
  implied probabilities and overrounds.
- **List:** History retains insertion order and repeated prices, filters by
  bookmaker, selects records at a time and supports successful removal.
- **Encapsulation:** Clearing externally returned collection copies leaves the
  actual history and market quotes intact.
- **Object interactions:** Providers create snapshots containing fixture,
  bookmaker and quote objects; history and comparison use those same records.
- **Ordinary negative results:** Explicitly unavailable prices still form
  incomplete markets. Future records, stale prices and kickoff remain normal
  comparison exclusions rather than exceptions.

## Verification

- `python main.py` completes with all state-preservation confirmations reporting
  `True` and the final successful home-price comparison.
- The demonstration's pytest test now checks feedback for all seven exception
  types, state confirmations and a successful comparison in the final section.
- The complete suite reports **129 passed**, with **99% overall coverage** when
  branch measurement is enabled.

Task 8, the final rubric and submission review, has not been started.
