"""Shared dashboard error value; no execution, persistence or transport imports."""
class DashboardExecutionError(ValueError):
    def __init__(self, code, message, status=400, details=None, *, prelaunch_not_started=False):
        super().__init__(message)
        self.code, self.message, self.status = code, message, status
        self.details = details or {}
        self.prelaunch_not_started = prelaunch_not_started is True
