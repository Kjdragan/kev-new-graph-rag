# Graffiti Extraction & Neo4j Ingestion Plan

## Notes

- Graffiti (Graphiti) expects all node and relationship property values to be
  primitive types or arrays (no nested dicts/objects).
- Bulk ingestion (`add_episode_bulk`) should NOT be used if edge invalidation is
  required; use `add_episode` instead for incremental/validated updates.
- The current pipeline uses a `GraphExtractor.extract()` method, passing
  ontology definitions and document text, and calls `add_episode` (not bulk) for
  each document. This matches Graphiti's guidance and avoids the pitfalls of
  bulk ingestion (no edge invalidation).
- The ontology has now been fully aligned with Graphiti documentation: no custom
  base classes, all node and relationship types are standard Pydantic models.
- The recent ImportError was due to legacy base class imports; this has been
  resolved by removing custom base classes and updating all references to use
  Pydantic's `BaseModel` directly.
- The Graffiti (Graphiti) ingestion pipeline is now fully operational. This was
  achieved by:
  1. Refactoring all ontology templates to use only Pydantic BaseModel,
     eliminating custom base classes and import errors.
  2. Ensuring all `name` fields in ontology models were renamed to avoid
     conflicts with protected attributes (e.g., `company_name`, `event_name`).
  3. Updating the ingestion pipeline to use only the async `add_episode` method,
     ensuring edge invalidation and incremental updates.
  4. Verifying that all properties passed to Graffiti are primitive types or
     arrays, not nested objects.
  5. Removing the test-only document limitation so all Drive files are ingested.
  6. Validating the pipeline end-to-end with two documents, confirming
     successful extraction of nodes and edges with no errors.
- Next steps: Document project structure, summarize extraction results, create a
  comprehensive .md report in the documentation directory, and ensure
  maintainability as a standalone project.
- If extractions are producing non-primitive properties, the issue is likely in
  how the extractor or ontology structures attributes (e.g., nested dicts in
  `properties` fields).
- The ingestion pipeline appears to follow Graphiti's recommended async,
  per-document ingestion pattern, but property flattening and validation must be
  checked in the extractor logic.
- Neo4j queries are failing due to missing labels (e.g., `Entity`) and
  properties (e.g., `name_embedding`, `summary`). This suggests the schema has
  changed or was deleted. Immediate investigation is required before further
  validation of ingested data.
- Resetting (clearing) the Neo4j database and re-ingesting using the pipeline
  with the generic ontology will ensure the database schema matches the
  ontology. This does NOT update queries in your application—those must be
  checked separately.
- If a full reset is insufficient (e.g., persistent label bubbles or
  connection/auth issues), deleting and recreating the Neo4j instance is
  recommended. This requires updating all relevant credentials and connection
  parameters in your `.env` file before re-running the pipeline.

## Task List

- [x] Review how extracted node and relationship properties are structured
      before ingestion (ensure all are primitives/arrays)
- [x] Ensure ontology templates and extractor logic do not allow nested objects
      in properties
- [x] Confirm that `add_episode` is used (not `add_episode_bulk`) unless edge
      invalidation is unnecessary
- [x] Refactor ontology and extractor to use only Pydantic models (no custom
      base classes)
- [x] Add property validation/flattening if needed in extractor
- [ ] Document and summarize current project structure and script
      interdependencies
- [ ] Summarize/extract what was ingested in this run for further validation
- [ ] Create a comprehensive .md report detailing the debugging and resolution
      journey for Graphiti ingestion (save to documentation directory)
- [ ] Investigate and restore missing Neo4j schema (labels/properties) required
      for queries
- [ ] Reset (clear) Neo4j database of all nodes and relationships
- [ ] Re-ingest data using the extraction pipeline and generic ontology
- [ ] Verify Neo4j contains only ontology-defined labels/properties
- [ ] Delete and recreate Neo4j instance if needed
- [ ] Update .env with new Neo4j credentials and connection info
- [ ] Reconnect and re-run ingestion pipeline with generic ontology

## Current Goal

Investigate, reset/recreate Neo4j, update .env, and re-ingest.
