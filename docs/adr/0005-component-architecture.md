# Modular Component Architecture

* Status: Accepted
* Deciders: FinPilot Development Team
* Date: 2025-01-18

## Context

The original `views/utils.py` had grown to 1200+ lines containing:

1. Formatting utilities
2. Validation logic
3. UI helpers
4. Data transformations
5. Helper functions

This created problems:
- Difficult to test individual components
- High cognitive load when reading
- Circular import risks
- Hard to find specific functionality
- No clear ownership of code sections

## Decision

Refactor into a modular component architecture:

```
views/
├── __init__.py
├── dashboard.py
├── settings.py
├── utils.py          # Reduced to re-exports
└── components/       # NEW
    ├── __init__.py
    ├── formatters.py
    ├── validators.py
    └── ui_helpers.py
```

### Component Responsibilities

| Component | Responsibility | LOC |
|-----------|---------------|-----|
| formatters.py | Number, date, currency formatting | ~150 |
| validators.py | Input validation, schema checks | ~200 |
| ui_helpers.py | Streamlit UI components | ~180 |

### Backward Compatibility

The original `utils.py` now re-exports from components:

```python
# views/utils.py
from views.components.formatters import (
    format_number,
    format_currency,
    format_percent,
)
from views.components.validators import (
    validate_ticker,
    validate_settings,
)
```

## Consequences

### Positive

* **Testability**: Each component can be tested in isolation
* **Readability**: Smaller, focused files (~150 LOC each)
* **Maintainability**: Clear ownership and boundaries
* **Reusability**: Components can be imported where needed
* **IDE Support**: Better autocomplete and navigation

### Negative

* **Import Paths**: Longer import paths for direct access
* **Migration Effort**: One-time refactoring work
* **Discovery**: New developers need to learn structure

### Neutral

* No performance impact (same code, different files)
* Total LOC unchanged

## Architecture Principles

### Single Responsibility

Each component does one thing well:

```python
# formatters.py - ONLY formatting
def format_number(value, decimals=2):
    """Format number with thousand separators."""
    pass

def format_percent(value, decimals=1):
    """Format as percentage with symbol."""
    pass
```

### Dependency Direction

```
views/dashboard.py
      ↓
views/utils.py (re-exports)
      ↓
views/components/formatters.py
views/components/validators.py
views/components/ui_helpers.py
      ↓
core/  (no view imports!)
```

### No Circular Dependencies

- Components don't import from views
- Views import from components
- Core doesn't know about views

## Alternatives Considered

### Option 1: Single Large File

Keep everything in `utils.py`.

**Pros:**
* No migration
* Simple imports

**Cons:**
* Hard to maintain
* Poor testability
* High cognitive load

**Verdict**: Rejected due to maintainability

### Option 2: Class-Based Organization

Group functions into classes.

**Pros:**
* Namespace organization
* Can use inheritance

**Cons:**
* Unnecessary OOP overhead
* Stateless functions don't need classes
* Python is not Java

**Verdict**: Rejected - over-engineering

### Option 3: Separate Package

Create `finpilot_utils` package.

**Pros:**
* Complete isolation
* Could be pip-installable

**Cons:**
* Overkill for internal code
* Version management overhead
* Deployment complexity

**Verdict**: Rejected - too complex

## Implementation

### Phase 1: Extract Components

```python
# views/components/formatters.py
def format_number(value: float, decimals: int = 2) -> str:
    """Format number with thousand separators."""
    if value is None:
        return "—"
    return f"{value:,.{decimals}f}"

def format_currency(value: float, symbol: str = "$") -> str:
    """Format as currency."""
    if value is None:
        return "—"
    return f"{symbol}{value:,.2f}"
```

### Phase 2: Update Imports

```python
# Before (direct)
from views.utils import format_number

# After (same works due to re-export)
from views.utils import format_number

# OR more explicit
from views.components.formatters import format_number
```

### Phase 3: Add Tests

```python
# tests/test_formatters.py
def test_format_number():
    assert format_number(1234.567) == "1,234.57"
    assert format_number(None) == "—"
    assert format_number(1000, decimals=0) == "1,000"
```

## References

* [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
* [Python Package Structure](https://docs.python-guide.org/writing/structure/)
* [Single Responsibility Principle](https://en.wikipedia.org/wiki/Single-responsibility_principle)
* Sprint 3 Refactoring Documentation
