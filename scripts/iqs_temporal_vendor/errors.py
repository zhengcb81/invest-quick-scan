"""Named refusals. Malformed/unknown inputs are errors, never silent fallbacks."""

from __future__ import annotations


class TimeSemanticsError(ValueError):
    """A named refusal from the time-semantics interpreter."""

    def __init__(self, error_code: str, detail: str = "") -> None:
        self.error_code = error_code
        self.detail = detail
        super().__init__(f"{error_code}: {detail}" if detail else error_code)


def bad(code: str, detail: str = "") -> TimeSemanticsError:
    return TimeSemanticsError(code, detail)
