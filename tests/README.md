# Graph RAG System Test Suite

This document provides an overview of the test suite for the Graph RAG system, including test organization, running instructions, and best practices for adding new tests.

## Test Organization

The test suite is organized into the following categories:

### Unit Tests
Located in `tests/utils/` directory, these tests verify the functionality of individual components with mocked dependencies:
- `test_embedding.py` - Tests for CustomGeminiEmbedding
- `test_document_parser.py` - Tests for DocumentParser 
- `test_neo4j_ingester.py` - Tests for Neo4jIngester
- `test_chroma_ingester.py` - Tests for ChromaIngester
- `test_gdrive_reader.py` - Tests for GDriveReader
- `test_edge_cases.py` - Tests for challenging scenarios like large documents, unusual formats, and API rate limits

### Integration Tests
Located in `tests/integration/` directory, these tests verify interactions between multiple components:
- `test_ingestion_pipeline.py` - Tests the document parsing → embedding → storage pipeline
- `test_hybrid_search_integration.py` - Tests the hybrid search engine (when implemented)

### End-to-End Tests
Located in `tests/` root directory, these tests verify complete workflows:
- `test_end_to_end_ingestion.py` - Tests the full document ingestion workflow from GDrive to ChromaDB and Neo4j

## Running Tests

All tests must be run using the `uv` package manager as per project requirements:

```bash
# Run all tests
uv run python run_tests.py --all

# Run only unit tests
uv run python run_tests.py --unit

# Run only integration tests
uv run python run_tests.py --integration

# Run specific module tests
uv run python run_tests.py --module tests.utils.test_edge_cases

# Generate coverage report
uv run python run_tests.py --all --coverage
```

## Pytest Markers

Tests are categorized using pytest markers in `pytest.ini`:

- `@pytest.mark.unit` - Unit tests with mocked dependencies
- `@pytest.mark.integration` - Tests that interact with external services
- `@pytest.mark.e2e` - End-to-end tests for complete workflows

## Test Environment

### Environment Variables

Tests use environment variables for configuration, typically loaded from `.env` files:

- `GOOGLE_API_KEY` - Required for Google Gemini API tests
- `LLAMA_CLOUD_API_KEY` - Required for LlamaParse API tests
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` - Required for Neo4j integration tests

For unit tests, these are typically mocked. Integration tests require actual credentials.

## Best Practices for Test Development

1. **Proper Mocking**:
   - Mock external dependencies correctly using `unittest.mock`
   - Mock at the import location (e.g., `utils.embedding.genai.Client`)
   - Use appropriate context managers for patch scopes

2. **Test Isolation**:
   - Each test should be independent and not rely on others
   - Use fixtures for common setup and teardown

3. **Test Coverage**:
   - Aim for comprehensive coverage of happy paths and error cases
   - Include edge cases for unusual inputs, rate limits, etc.

4. **Test Data**:
   - Use realistic sample data for tests
   - Create reusable fixtures for common test data

5. **Assertions**:
   - Be specific with assertions to catch subtle bugs
   - Verify both function return values and side effects

## Adding New Tests

When adding new tests:

1. Place the test in the appropriate category directory
2. Add the correct pytest marker (`@pytest.mark.unit`, etc.)
3. Follow the naming convention: `test_*.py` for files, `test_*` for functions
4. Create or reuse fixtures for common setup
5. Run the tests to verify they work as expected

## Troubleshooting

Common issues and solutions:

- **Test failures due to API changes**: Update mocks to match current API responses
- **Dependency issues**: Ensure all dependencies are installed via `uv add`
- **Environment variable issues**: Verify `.env` file is properly loaded or use monkeypatch in tests
- **Test isolation problems**: Check for test dependencies or side effects
