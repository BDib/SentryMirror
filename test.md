# 🧪 SentryMirror Testing Documentation

This document tracks the current test coverage and instructions for the SentryMirror project.

## Running Tests
Ensure you have `pytest` installed:
```bash
pip install pytest

```

Run all tests from the project root:

```bash
pytest

```

## Coverage Overview

| Module | Test File | Status | Description |
| --- | --- | --- | --- |
| `database.py` | `tests/test_database.py` | ✅ Active | Validates JSON-to-SQL schema inference. |
| `audit.py` | `tests/test_audit.py` | 🏗️ In-Progress | Structural validation of header results. |
| `api.py` | `tests/test_api_scaffold.py` | 📝 Planned | Testing simulated routes with TestClient. |
| `database.py` | `tests/test_db_temp_fixture.py` | 📝 Planned | Testing Temp Database Fixture. |

---

## 📋 Future Testing Roadmap

* [ ] **Integration Tests**: Use a `pytest` fixture to spin up a temporary local web server and verify that `Crawler` correctly captures and saves assets.
* [ ] **Mocked Audits**: Update `test_audit.py` to use `unittest.mock` to simulate various HTTP header responses (missing vs. present).
