from Shared.Logger import LogItemTracker
from Shared.Settings import Settings


class LogObject:

    def __init__(self, parent, name):
        if Settings.get_bool("state_logging"):
            parent_id = 0
            if parent is not None:
                parent_id = parent.log_tracker.id
            self.log_tracker = LogItemTracker(parent_id, name)

    def __setattr__(self, name, value):
        if Settings.get_bool("state_logging"):
            self.process_update(name, value)
        super().__setattr__(name, value)

    def process_update(self, name, value):
        if not hasattr(self, "log_tracker") or self.log_tracker is None:
            return

        if name.startswith("_"):
            return

        if not isinstance(value, (str, int, float, bool)):
            return

        if hasattr(self, name) and getattr(self, name) == value:
            return

        self.log_tracker.update(name, value)

    def finish(self):
        if Settings.get_bool("state_logging"):
            self.log_tracker.finish()


def log_wrapper(prop):
    def wrapper_decorator(func):
        def func_wrapper(sender, value):
            if getattr(sender, prop) != value:
                sender.log_tracker.update(prop, value)
            func(sender, value)

        return func_wrapper

    return wrapper_decorator
