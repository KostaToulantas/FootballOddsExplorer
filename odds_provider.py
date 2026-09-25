from abc import ABC, abstractmethod


class OddsProvider(ABC):
    """Common behaviour required of a source of market snapshots."""

    def __init__(self, source_name):
        self._source_name = source_name

    @abstractmethod
    def load_snapshot(self):
        pass

    def __str__(self):
        return self._source_name
