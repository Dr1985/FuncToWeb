from func_to_web import run, Params

# Params subclasses are frozen dataclasses, so cross-field validation goes in
# __post_init__. A ValueError raised there surfaces in the form as a 422.

class DateRange(Params):
    start: int = 0
    end:   int = 10

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("start must be <= end")
        # Derive a field on a frozen instance with object.__setattr__.
        object.__setattr__(self, "span", self.end - self.start)

def report(rng: DateRange):
    return f"Range {rng.start}..{rng.end} (span {rng.span})"

run(report)
