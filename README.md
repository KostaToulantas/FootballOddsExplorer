# Football Odds Explorer

Task 4 foundation, using the supplied course content through Topic 7. Run from this folder with:

```text
python main.py
```

The demonstration uses fictional football odds. It constructs fixtures, bookmakers and market snapshots, calculates implied probabilities and overround, records price movement, and compares prices before kickoff. No packages need installing.

Kickoff, snapshot recording times, and history/comparison query times use timezone-aware Python `datetime` objects. The fictional demo takes place on 25 September 2026, with kickoff at 7:30 pm UTC and a comparison at 7:15 pm UTC. Displayed times include their timezone. Quote age limits remain integer minutes; the comparator uses `timedelta` to compare elapsed time. These classes are part of Python's standard library and need no installation.

## Course scope

The implementation uses classes, constructors, methods, modules and string conversions (Topics 1–2); private attributes and relationships (Topic 3); properties, composition, equality and helper methods (Topic 4); inheritance, overriding, protected state and `super()` (Topic 5); and an abstract provider (Topic 7). It does not introduce multiple inheritance because the model has no need for it.

Each class has its own module. A snapshot creates and owns its three quotes (composition), but shares its fixture and bookmaker (association). A history holds existing snapshots (aggregation). Read-only properties protect recorded prices and timestamps from ordinary reassignment. The comparator's maximum quote age is editable through a validated property because it is a user preference. Invalid updates leave its previous value unchanged; invalid initial ages leave the default of zero.

`OddsQuote` represents an invalid price with `None`. Incomplete markets cannot be compared and have no overround. Methods return `False` or `None` for unsupported operations or unavailable results, without using Topic 10 exception handling. Constructors otherwise expect the documented object and primitive types.

## Changes from the initial UML

The original `.drawio` file and PNG remain the initial design. The course export explicitly places lists, sets and dictionaries in Topic 8 and recommends individual attributes before that topic. These foundation differences keep the implementation within the requested scope:

| Initial model | Foundation implementation |
| --- | --- |
| `datetime` and `timedelta` | Actual dates and times, as requested, using the standard library beyond the supplied course topics. The maximum quote age setting remains integer minutes. |
| Snapshot quote dictionary and `prices` argument | Three owned quote attributes and separate `home`, `draw`, `away` constructor arguments. |
| History snapshot list | Two snapshot attributes; adding a third returns `False`. Removal frees a slot. |
| `filter_by_bookmaker()` returning a list | Deferred; `latest_at()` already searches the two slots for the specified bookmaker. |
| `compare(snapshots, as_of)` returning a dictionary | `compare(first, second, outcome, as_of)` returns the best snapshot for one outcome. Ties keep the first argument. |
| `load_snapshots()` and sample records list | `load_snapshot()` returns one newly constructed snapshot. Each sample provider holds one set of prices. |
| `CsvOddsProvider` | Deferred entirely: CSV loading is not covered in the supplied Topics 1–7. The abstract provider and working sample subclass establish the inheritance relationship now. |

Comparison requires matching fixture IDs, complete markets, a recording time at or before the comparison time, and an age no greater than the configured limit. Kickoff itself is excluded. History queries return the latest stored record at or before the requested time, without applying the comparator's freshness rule. Price change is the end price minus the start price; a missing record or invalid outcome gives `None`.

Later work can replace the two history slots with a list, store outcomes and comparison results in dictionaries, and add CSV loading when the relevant concepts are permitted. The current version handles one comparison between two markets at a time and does not fetch live odds.

The supplied `Workshop 7-1.docx` was zero bytes when inspected. Requirements were read from the supplied Canvas export and UML. This implementation addresses Task 4; it does not claim a peer review or completion of other workshop tasks.
