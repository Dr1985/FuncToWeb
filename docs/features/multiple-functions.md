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

Each function is reachable at its own `/<slug>` URL. Duplicate URLs raise a
clear error at startup.

## Custom App Title

```python
run([func1, func2], app_title="My Internal Tools")
```
