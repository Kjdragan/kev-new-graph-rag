# Framework Integration Architecture

This document explains how the various frameworks in our Graph RAG system work together, their specific responsibilities, and where they complement each other.

## Core Frameworks

Our system architecture integrates three primary frameworks, each with distinct responsibilities:

### 1. Graphiti-core

**Primary Role**: Temporal knowledge graph construction and management

**Key Responsibilities**:
- Episodic data ingestion from various sources (text, JSON, messages)
- Entity and relationship extraction with temporal metadata
- Bi-temporal model tracking relationship lifecycles (t_valid/t_invalid)
- Custom Pydantic-defined entity types for domain-specific knowledge
- Hybrid search capabilities (semantic, keyword, graph traversal)

**When to Use**:
- For adding new information to the knowledge graph
- For temporal queries requiring historical context
- For tracking how relationships evolve over time
- For custom entity type definition and extraction

### 2. Neo4j AuraDB

**Primary Role**: Persistent graph database storage

**Key Responsibilities**:
- Physical storage of the knowledge graph
- ACID-compliant transaction processing
- Native graph data model with nodes, relationships, and properties
- Cypher query execution engine
- Indexing and constraint management

**When to Use**:
- As the underlying storage layer for both Graphiti and Llama-Index
- For direct Cypher queries when performance-critical operations are needed
- For database administration tasks (index management, constraint setup)

### 3. Llama-Index

**Primary Role**: LLM orchestration and RAG pipeline management

**Key Responsibilities**:
- Knowledge graph construction from unstructured text (complementary to Graphiti)
- Text2Cypher translation for natural language querying
- Pre-built RAG patterns and query engines
- Vector search capabilities and hybrid search strategies
- Integration with multiple LLM providers (focusing on Gemini for our project)

**When to Use**:
- For natural language understanding and query translation
- For standardized RAG retrieval patterns
- For response synthesis using the retrieved knowledge
- For hybrid search combining semantic and graph-based retrieval

## Integration Points

The following diagram illustrates how these frameworks connect:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  User Interface │     │      Query      │     │    Knowledge    │
│   (Streamlit)   │◄───►│   Processing    │◄───►│    Storage      │
│                 │     │  (Llama-Index)  │     │  (Neo4j/Graphiti)│
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                              ▲
                              │
                              ▼
                        ┌─────────────────┐
                        │                 │
                        │  LLM Services   │
                        │    (Gemini)     │
                        │                 │
                        └─────────────────┘
```

### Key Integration Flows:

1. **Data Ingestion Flow**:
   ```
   Raw Data → Graphiti Processing → Neo4j Storage
   ```

2. **Query Processing Flow**:
   ```
   Natural Language Query → Llama-Index Text2Cypher → Neo4j Query → 
   Results Retrieval → Llama-Index Response Synthesis → User Interface
   ```

3. **Knowledge Graph Construction**:
   ```
   Unstructured Text → Llama-Index KG Extraction → Neo4j Storage ↔ Graphiti Temporal Management
   ```

## Framework-Specific Integration Details

### Graphiti-Neo4j Integration

The Graphiti-Neo4j integration is direct, with Graphiti acting as a client application to Neo4j:

```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    neo4j_uri="bolt://...",
    neo4j_username="neo4j",
    neo4j_password="password"
)
```

Graphiti manages temporal aspects of the graph and provides high-level APIs for episodic data processing, while offloading the actual storage to Neo4j.

### Llama-Index-Neo4j Integration

Llama-Index connects to Neo4j through the `Neo4jGraphStore` adapter:

```python
from llama_index.graph_stores.neo4j import Neo4jGraphStore
from llama_index.core.indices.knowledge_graph import KnowledgeGraphIndex

graph_store = Neo4jGraphStore(
    url=neo4j_uri,
    username=neo4j_username,
    password=neo4j_password
)

kg_index = KnowledgeGraphIndex.from_documents(
    documents,
    storage_context=StorageContext.from_defaults(graph_store=graph_store)
)
```

This allows Llama-Index to both write to and read from the Neo4j database without directly interacting with Graphiti.

### Graphiti-Llama-Index Coordination

While Graphiti and Llama-Index don't directly integrate with each other, they can coexist by:

1. Operating on the same Neo4j database
2. Using separate namespaces or labels to avoid conflicts
3. Leveraging each framework's strengths for different aspects of the system

This coordination happens at the application level rather than through direct API integration.

## When to Use Which Framework

| Task | Recommended Framework | Reason |
|------|----------------------|--------|
| Initial data ingestion | Graphiti | Better temporal modeling and episodic processing |
| Custom entity type definition | Graphiti | Native support for Pydantic models as entity types |
| Knowledge extraction from text | Llama-Index | Specialized for LLM-based extraction patterns |
| Natural language querying | Llama-Index | Strong text2cypher capabilities |
| Temporal relationship tracking | Graphiti | Core feature of its bi-temporal model |
| Response generation | Llama-Index | Well-established RAG patterns |
| Direct graph queries | Neo4j (Cypher) | Most efficient for complex graph traversals |
| Multi-modal RAG | Llama-Index | Built-in support for multi-modal retrievers |

## Framework Selection Guidelines

When implementing a feature, consider these guidelines:

1. **For Knowledge Building**:
   - Use **Graphiti** when temporal tracking is important
   - Use **Llama-Index** when extracting from complex unstructured text

2. **For Queries**:
   - Use **Llama-Index** for natural language understanding and RAG pipelines
   - Use direct **Neo4j/Cypher** queries for performance-critical operations
   - Use **Graphiti** for temporal queries that need to consider historical states

3. **For LLM Integration**:
   - Use **Llama-Index** for structured output and response synthesis
   - Use **Graphiti** with its built-in LLM clients for entity extraction

## Conclusion

Our Graph RAG system leverages the complementary strengths of Graphiti, Neo4j, and Llama-Index:

- **Graphiti**: Excels at temporal knowledge management and episodic processing
- **Neo4j**: Provides robust graph storage and querying capabilities
- **Llama-Index**: Specializes in LLM orchestration and RAG patterns

By using these frameworks in their areas of strength, we create a comprehensive system that handles both historical knowledge tracking and advanced retrieval-augmented generation.
