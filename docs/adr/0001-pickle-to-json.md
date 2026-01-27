# Migrate from Pickle to JSON for Data Persistence

* Status: Accepted
* Deciders: FinPilot Development Team
* Date: 2025-01-15

## Context

The system was using Python's `pickle` module for serializing user settings, scan results, and cached data. This created several problems:

1. **Security Risk**: Pickle can execute arbitrary code during deserialization, making it vulnerable to code injection attacks
2. **Interoperability**: Pickle files can only be read by Python, limiting integration options
3. **Version Brittleness**: Pickle files can break when Python or library versions change
4. **Debugging Difficulty**: Binary pickle files cannot be easily inspected or modified

With the system moving toward production deployment, these risks became unacceptable.

## Decision

Replace all pickle-based persistence with JSON serialization:

1. **User Settings**: `user_settings.json` (was `.pickle`)
2. **Model Metadata**: `model_metadata.json` (was `.pickle`)
3. **Cache Data**: JSON format with atomic writes
4. **Scan Results**: CSV + JSON metadata

Implementation details:
- Use `orjson` for fast JSON serialization
- Implement atomic writes with temp files
- Add schema validation for JSON data
- Create migration script for existing pickle files

## Consequences

### Positive

* **Security**: Eliminated arbitrary code execution risk
* **Debugging**: Settings can be inspected/edited with any text editor
* **Interoperability**: Data can be consumed by JavaScript, Go, etc.
* **Stability**: JSON format is stable across Python versions
* **Git-friendly**: JSON diffs are readable in version control

### Negative

* **Performance**: JSON is slightly slower than pickle for complex objects (mitigated by orjson)
* **Type Limitations**: Some Python types (datetime, numpy arrays) need custom handling
* **Migration Effort**: Required one-time migration of existing data

### Neutral

* File sizes are comparable for our use cases
* Both formats support compression if needed

## Alternatives Considered

### Option 1: MessagePack

Binary format with JSON-like semantics.

**Pros:**
* Faster than JSON
* Smaller file sizes
* Cross-language support

**Cons:**
* Binary format (harder to debug)
* Less common than JSON
* Requires additional dependency

**Verdict**: Rejected due to debugging difficulty

### Option 2: YAML

Human-readable format.

**Pros:**
* Very readable
* Supports comments
* Good for configuration

**Cons:**
* Slower than JSON
* Security concerns (arbitrary code execution possible)
* Multiple specs/implementations

**Verdict**: Rejected due to security concerns and complexity

### Option 3: SQLite

Embedded database.

**Pros:**
* SQL queries
* ACID transactions
* Single file

**Cons:**
* Overkill for our needs
* Binary format
* Larger dependency

**Verdict**: Rejected as unnecessarily complex

## Implementation

```python
# Before
with open('settings.pickle', 'wb') as f:
    pickle.dump(settings, f)

# After
from core.persistence import save_json
save_json('settings.json', settings)  # Atomic write, validated
```

## References

* [OWASP: Deserialization Vulnerabilities](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/15-Testing_for_HTTP_Incoming_Requests)
* [Python Pickle Security](https://docs.python.org/3/library/pickle.html#restricting-globals)
* Sprint 1 Security Audit Report
