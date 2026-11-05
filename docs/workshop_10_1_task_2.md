# Workshop 10-1: Task 2 - Create Custom Exceptions

The exceptions in `odds_exceptions.py` represent the seven situations recorded in
Task 1. Each inherits from `OddsExplorerError`, which inherits from `Exception`.
This shared parent allows later application behaviour to catch the domain errors
as a group, while individual classes allow specific recovery where needed.

| Task 1 situation | Custom exception | Information included in its message |
| --- | --- | --- |
| Invalid decimal odds | `InvalidDecimalOddsError` | Outcome, rejected value and the finite-number-greater-than-1 rule |
| Invalid maximum quote age | `InvalidQuoteAgeError` | Rejected value, integer requirement, minimum of zero and units in minutes |
| Snapshot from a different fixture | `FixtureMismatchError` | Requested operation, expected fixture ID and actual fixture ID |
| Same snapshot object added twice | `DuplicateSnapshotError` | Fixture ID, bookmaker and recording time |
| Snapshot absent when removing | `SnapshotNotFoundError` | History's fixture ID, bookmaker and recording time |
| Unsupported outcome | `UnknownOutcomeError` | Requested outcome and supported outcome keys |
| Reversed price-change interval | `InvalidTimeRangeError` | Start and end timestamps and their required order |

Rejected values in odds, age and outcome messages use `repr` formatting so a
string such as `"2.20"` can be distinguished from the numeric value `2.20`.
Timestamp messages retain the timezone information supplied by the caller.

This task defines the classes and their messages only. Raising them from rule
enforcement methods belongs to Task 3, recovery belongs to Task 4, and extending
the pytest suite to check raised exceptions belongs to Task 5. Existing class
behaviour and `main.py` are unchanged.
