# Testing Strategy for Kevin-Graph-RAG

This document outlines the testing approach for the Kevin-Graph-RAG project, including unit and integration tests.

## Test Organization

The project uses pytest with the following organization:

- `tests/`: Main test directory
  - `test_*.py`: Unit tests (run with mocks)
  - `integration/test_*.py`: Integration tests (connect to real services)
  - `conftest.py`: Shared test fixtures and configuration

## Running Tests

All tests use `pytest` through UV package manager:

### Unit Tests

These tests use mocks and do not require external services:

```bash
uv run pytest -m "unit" -xvs
```

### Integration Tests

These tests connect to real Neo4j and Google Gemini APIs:

```bash
uv run pytest -m "integration" -xvs
```

### All Tests

To run all tests:

```bash
uv run pytest -xvs
```

## Test Requirements

### Unit Tests

- No external dependencies required
- Mocks are set up automatically
- Fast execution, suitable for CI/CD

### Integration Tests

Integration tests require:

1. A populated Neo4j database (run `scripts/llama_kg_construction_test.py` first)
2. Valid `.env` file with:
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
   - `GOOGLE_API_KEY`

Integration tests will be automatically skipped if:
- `.env` file is missing
- Neo4j connection fails
- Google API key is invalid

## Test Architecture

### Unit Tests

Unit tests mock all external dependencies:
- Neo4j driver
- Google Gemini models
- Embedding models
- Configuration

This ensures tests run quickly and don't depend on external services.

### Integration Tests

Integration tests use real services to validate:
- Neo4j queries work correctly
- Embedding generation is accurate
- LLM responses are meaningful
- End-to-end query processing works

These tests are more thorough but slower and require credentials.

## Adding New Tests

When adding new functionality:

1. Write unit tests first with proper mocks
2. Then add integration tests to verify real-world behavior
3. Add appropriate pytest markers to new test files

## Continuous Integration

Tests are organized to support CI/CD workflows:
- Unit tests can run on every PR
- Integration tests can run on selected branches with secure credentials
