from Shared.Logger import LogItemTracker


class LogObject:

    def __init__(self, parent, name):
        parent_id = 0
        if parent is not None:
            parent_id = parent.log_tracker.id
        self.log_tracker = LogItemTracker(parent_id, name)

    def __setattr__(self, name, value):
        if hasattr(self, "log_tracker"):
            if not name.startswith("_") and isinstance(value, (str, int, float, bool)):
                self.log_tracker.update(name, value)
        super().__setattr__(name, value)

    def finish(self):
        self.log_tracker.finish()


def log_wrapper(prop):
    def wrapper_decorator(func):
        def func_wrapper(sender, value):
            if getattr(sender, prop) != value:
                sender.log_tracker.update(prop, value)
            func(sender, value)

        return func_wrapper

    return wrapper_decorator
