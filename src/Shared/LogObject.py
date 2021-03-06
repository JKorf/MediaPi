from enum import Enum

from Shared.Logger import LogItemTracker
from Shared.Settings import Settings


class LogObject:

    def __init__(self, parent, name):
        self._logging = Settings.get_bool("state_logging")
        if self._logging:
            parent_id = 0
            if parent is not None:
                parent_id = parent.log_tracker.id
            self.log_tracker = LogItemTracker(parent_id, name)

    def __setattr__(self, name, value):
        if hasattr(self, "_logging") and self._logging:
            self.process_update(name, value)
        super().__setattr__(name, value)

    def process_update(self, name, value):
        if not hasattr(self, "log_tracker") or self.log_tracker is None:
            return

        if name.startswith("_"):
            return

        if hasattr(self, name) and getattr(self, name) == value:
            return

        if not isinstance(value, (str, int, float, bool)):
            if isinstance(value, Enum):
                value = str(value)
            else:
                return

        self.log_tracker.update(name, value)

    def finish(self):
        if self._logging:
            self.log_tracker.finish()
