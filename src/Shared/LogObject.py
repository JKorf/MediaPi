from Shared.Logger import LogItemTracker


class LogObject:

    def __init__(self, parent, name):
        parent_id = 0
        if parent is not None:
            parent_id = parent.log_tracker.id
        self.log_tracker = LogItemTracker(parent_id, name)

    def update_log(self, name, value):
        self.log_tracker.update(name, value)


def log_wrapper(prop):
    def wrapper_decorator(func):
        def func_wrapper(sender, value):
            if getattr(sender, prop) != value:
                sender.log_tracker.update(prop, value)
            func(sender, value)

        return func_wrapper

    return wrapper_decorator
