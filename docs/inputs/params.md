# Params

`Params` is a base class that tells FuncToWeb to expand its annotated fields into the form automatically. Subclassing it turns your class into a **frozen dataclass**: instances are constructible with keyword arguments, comparable, hashable and immutable. If you know the `dataclasses` standard library, you already know `Params`.

## Basic Usage

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run, Params
from func_to_web.types import Email

class UserData(Params):
    name:  Annotated[str, Field(min_length=2, max_length=50)]
    email: Email
    age:   int = 18

def basic(data: UserData):
    return f"Created: {data.name}, {data.email}, {data.age}"

run(basic)
```

FuncToWeb expands `UserData` into three individual form fields — `name`, `email`, and `age` — exactly as if you had declared them directly on the function.

![Basic Usage](../images/params1.jpg)

## Reusing Across Functions

The main use case for `Params` is sharing the same fields across multiple functions without repeating yourself:

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run, Params
from func_to_web.types import Email

class UserData(Params):
    name:  Annotated[str, Field(min_length=2, max_length=50)]
    email: Email

def create_user(data: UserData):
    return f"Created: {data.name}"

def edit_user(id: int, data: UserData):
    return f"Edited user {id}: {data.name}"

run([create_user, edit_user])
```

Change `UserData` once and it updates every function that uses it.

![Creating Users](../images/params2.jpg)
![Editing Users](../images/params3.jpg)

## It's a Frozen Dataclass

Subclassing `Params` applies `@dataclass(frozen=True)` for you. Instances behave like any frozen dataclass — constructible anywhere, comparable by value, hashable, and immutable:

```python
from func_to_web import Params
from func_to_web.types import Email

class UserData(Params):
    name:  str
    email: Email

UserData(name="Ana", email="a@b.com")   # build one anywhere — tests, scripts
# == compares by value, instances are hashable, repr is readable
# data.name = "other"  -> raises FrozenInstanceError (immutable)
```

You can still add methods, properties and class variables — FuncToWeb reads only the **type-annotated fields**; everything else is ignored by the form renderer:

```python
class UserData(Params):
    name:  str
    email: Email

    @property
    def display(self):
        return f"{self.name} <{self.email}>"
```

![It's a Frozen Dataclass](../images/params4.jpg)

### Cross-field validation with `__post_init__`

Validation that spans more than one field goes in `__post_init__`. A `ValueError` raised there surfaces in the form as a **422 validation error**:

```python
from func_to_web import run, Params

class Range(Params):
    start: int = 0
    end:   int = 10

    def __post_init__(self):
        if self.start > self.end:
            raise ValueError("start must be <= end")

def use_range(r: Range):
    return f"Range: {r.start}..{r.end}"

run(use_range)
```

To derive a field inside `__post_init__`, assign it with `object.__setattr__` (the standard pattern for frozen dataclasses, since direct assignment is blocked):

```python
def __post_init__(self):
    object.__setattr__(self, "span", self.end - self.start)
```

### Variants with `dataclasses.replace()`

Instances are immutable, so to get a modified copy use `dataclasses.replace()` instead of mutating:

```python
from dataclasses import replace

base = UserData(name="Ana", email="a@b.com")
other = replace(base, name="Bob")   # new instance; base is untouched
```

## Mixing Params with Other Parameters

```python
from typing import Annotated
from pydantic import Field
from func_to_web import run, Params

class Address(Params):
    street: str
    city:   str
    zip:    Annotated[str, Field(pattern=r'^\d{5}$')]

def mixing(user_id: int, address: Address, notify: bool = True):
    return f"User {user_id} registered at {address.city}"

run(mixing)
```

## Default Values

Default values work exactly as in any Python class:

```python
from func_to_web import run, Params

class Settings(Params):
    theme:    str = "dark"
    language: str = "en"
    retries:  int = 3

def defaults(settings: Settings):
    return f"Theme: {settings.theme}, Lang: {settings.language}"

run(defaults)
```
