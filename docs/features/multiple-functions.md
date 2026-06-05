# Multiple Functions

Pass a list of functions to create an index page with navigation:

```python
from func_to_web import run

def calculate_bmi(weight_kg: float, height_m: float):
    """Calculate Body Mass Index"""
    return f"BMI: {weight_kg / (height_m ** 2):.2f}"

def celsius_to_fahrenheit(celsius: float):
    """Convert Celsius to Fahrenheit"""
    return f"{celsius}°C = {(celsius * 9/5) + 32}°F"

run([calculate_bmi, celsius_to_fahrenheit])
```

If only one function exists, the index page is skipped and it opens directly.

## Groups

Organize functions into collapsible groups by passing a list where each
group is a dict with **exactly one key** (the group name) and a list as the
value:

```python
from func_to_web import run

def add(a: int, b: int): return a + b
def multiply(a: int, b: int): return a * b
def upper(text: str): return text.upper()
def lower(text: str): return text.lower()

run([
    {"Math": [add, multiply]},
    {"Text": [upper, lower]},
])
```

Groups can be **nested** and freely mixed with plain functions at any level:

```python
run([
    standalone_func,
    {"Math": [
        add,
        multiply,
        {"Trig": [sin, cos]},   # nested subgroup
    ]},
    {"Text": [upper, lower]},
])
```

Group names are slugified and prefixed onto each function's URL, so
`add` inside `{"Math": [...]}` is reachable at `/math/add`, and `sin`
inside `{"Math": [{"Trig": [sin]}]}` at `/math/trig/sin`. Functions placed
at the top level keep their plain `/<slug>` URL. Duplicate URLs raise a
clear error at startup.

## Custom App Title

```python
run([func1, func2], app_title="My Internal Tools")
```
