# Technical Product Requirements Document: Comprehensive Graph RAG System

## 1. Introduction

This document outlines the technical requirements for building a comprehensive Graph Retrieval Augmented Generation (RAG) system for personal use. The system will leverage Graphiti-core for dynamic, temporal knowledge graph management, Neo4j AuraDB for persistent graph storage, Llama-Index for LLM orchestration, and Gemini Pro 2.5 on Vertex AI for advanced reasoning. The user interface will be a Streamlit-based chat application. The project aims to create a powerful, context-aware AI agent capable of interacting with a dynamic knowledge base.

## 2. Technical Architecture

### 2.1. System Components

1.  **Graphiti-core**: 
    *   Role: Real-time, temporal knowledge graph memory. Continuous ingestion of data (structured JSON, unstructured text, user interactions), entity/relationship extraction, and management of temporal updates (t_valid, t_invalid).
    *   Key Features: Bi-temporal model, Pydantic-defined custom entity types, hybrid search (semantic, keyword, graph traversal).
2.  **Neo4j AuraDB**: 
    *   Role: Scalable cloud graph database for persistent storage of the knowledge graph created and managed by Graphiti-core.
    *   Key Features: Native graph data model, managed service, ACID transactions, Python driver support.
3.  **Llama-Index**: 
    *   Role: LLM orchestration framework. Facilitates knowledge graph construction from text, hybrid search, and natural language querying over the Neo4j graph.
    *   Key Features: `Neo4jGraphStore`, `KnowledgeGraphIndex`, `PropertyGraphIndex`, text2cypher, advanced RAG patterns (hybrid search, metadata filtering).
4.  **Gemini Pro 2.5 (Vertex AI)**:
    *   Role: Advanced reasoning LLM.
    *   Key Features: "Thinking mode," structured output (for Pydantic model compatibility), 1 million token context window, multimodal capabilities (though initial focus is text).
5.  **Streamlit**: 
    *   Role: Framework for building the interactive chat interface for the MVP.
    *   Key Features: `st.chat_message`, `st.chat_input`, `st.session_state` for managing conversational flow and history.
6.  **Google Agent Development Kit (ADK)**:
    *   Role: Framework for building modular, multi-agent systems. To be used for intelligent query assistance, decomposition, and tool orchestration.
    *   Key Features: LLM-driven dynamic routing, tool definition (exposing Graph RAG query functions).
7.  **Model Context Protocol (MCP)**:
    *   Role: Open standard for AI models to interact with external tools/data. Graphiti-core includes an MCP server; ADK agents can act as MCP clients.
    *   Key Features: Standardized data ingestion, tool calling, secure connections.

### 2.2. Data Models

*   **Pydantic Models**: Central to data consistency. Used for:
    *   Defining custom entity types and their attributes within Graphiti-core. This guides LLM extraction and ensures structured data in Neo4j.
    *   Defining structured output schemas for Gemini Pro 2.5, ensuring reliable, machine-readable responses for graph updates or API integrations.
    *   Potentially for data validation within Llama-Index pipelines and ADK tool inputs/outputs.
*   **Graph Model (Neo4j/Graphiti)**:
    *   Nodes: Represent entities (e.g., concepts, persons, documents, chat messages).
    *   Edges: Represent relationships between entities (triplets: subject-predicate-object). Edges will include `t_valid` and `t_invalid` properties managed by Graphiti for temporal awareness.
    *   Properties: Attributes associated with nodes and edges (e.g., text content, embeddings, timestamps, custom entity attributes).

### 2.3. APIs and Integrations

*   **Graphiti-core & Neo4j**: Graphiti interacts directly with Neo4j AuraDB via the Python driver to persist and query graph data.
*   **Llama-Index & Neo4j**: Llama-Index uses `Neo4jGraphStore` to connect to AuraDB for graph operations and indexing.
*   **Llama-Index & Gemini**: Llama-Index will be configured to use Gemini Pro 2.5 as its primary LLM for tasks like text2cypher, KG extraction, and response generation.
*   **Streamlit & Backend**: Streamlit UI will call backend functions that orchestrate Llama-Index, ADK, and direct Gemini calls.
*   **ADK & Tools**: ADK agents will use Gemini for reasoning and will call tools, which will be Python functions wrapping:
    *   Llama-Index query engines.
    *   Direct Graphiti search/query functions.
    *   MCP client calls to other services (if applicable later).
*   **Gemini Pro 2.5 API**: Accessed via the Google Gen AI SDK (`google-genai`) using Application Default Credentials or API key (as per `.env`).
*   **MCP**: 
    *   Graphiti-core will run its MCP server component.
    *   ADK agents can be developed as MCP clients to interact with Graphiti or other potential MCP-compliant services.

### 2.4. Infrastructure Requirements

*   **Local Development Environment**:
    *   Python (latest stable version).
    *   `uv` for package management.
    *   Git for version control.
    *   IDE (e.g., VS Code).
*   **Cloud Services (as per `.env` and project needs)**:
    *   **Neo4j AuraDB**: Primary graph database (credentials in `.env`).
    *   **Google Cloud Platform (GCP) - Vertex AI**: For hosting/accessing Gemini Pro 2.5 (Project ID and location in `.env`).
    *   **Supabase**: Available (credentials in `.env`), potential for user authentication or other backend services if needed later, but not core to MVP RAG.
*   **API Keys**: As listed in `.env` for various LLMs (Anthropic, Perplexity, OpenAI, Google). Gemini Pro 2.5 via Vertex AI will be the primary focus.

## 3. Development Roadmap

### 3.1. Phase 1: Core Graph RAG MVP

1.  **Environment Setup & Configuration**:
    *   Initialize project structure, Git repository.
    *   Set up `uv` virtual environment.
    *   Configure `.env` file with necessary API keys and service credentials (already partially done).
2.  **Neo4j AuraDB Connection**:
    *   Establish and test connection to Neo4j AuraDB instance from Python.
3.  **Graphiti-core Basic Setup**:
    *   Integrate Graphiti-core library.
    *   Implement basic data ingestion into Graphiti (e.g., from a sample text file or string).
    *   Verify graph creation in Neo4j with temporal properties.
    *   Define 1-2 simple Pydantic models for custom entity extraction with Graphiti.
4.  **Llama-Index Integration - KG & Querying**:
    *   Configure Llama-Index with `Neo4jGraphStore` pointing to AuraDB.
    *   Set up Gemini Pro 2.5 as the LLM for Llama-Index.
    *   Implement document loading and `KnowledgeGraphIndex` creation from sample documents, persisting to Neo4j.
    *   Implement basic natural language querying using `KnowledgeGraphQueryEngine` (text2cypher and graph RAG).
5.  **Streamlit Chat Interface (MVP)**:
    *   Create a simple Streamlit UI with `st.chat_input` and `st.chat_message`.
    *   Connect UI to the Llama-Index query engine.
    *   Display LLM responses in the chat.
    *   Basic session state management for chat history.
6.  **Basic Hybrid Search**: 
    *   Ensure `include_embeddings=True` in `KnowledgeGraphIndex`.
    *   Implement a basic hybrid query that combines vector search with graph traversal through Llama-Index.

### 3.2. Phase 2: Enhancing Agentic Capabilities

1.  **Graphiti - Continuous Ingestion & Custom Entities**:
    *   Implement a mechanism to continuously ingest chat interactions into Graphiti for long-term memory.
    *   Expand Pydantic models for more diverse custom entity types relevant to potential use cases.
2.  **Gemini - Structured Output & Thinking Mode**:
    *   Leverage Gemini's structured output with Pydantic models for reliable graph updates from LLM reasoning.
    *   Explore Gemini's "Thinking mode" for more complex query understanding before tool use or graph interaction.
3.  **Google ADK - Basic Agent**:
    *   Set up a simple ADK agent.
    *   Define a Python function that uses the Llama-Index query engine as an ADK tool.
    *   Integrate the ADK agent into the Streamlit chat flow (e.g., user query goes to ADK agent, which then uses the RAG tool).
4.  **MCP - Graphiti Server & Basic Client**:
    *   Run the Graphiti-core MCP server.
    *   Develop a simple MCP client (can be part of an ADK tool or a standalone test script) to list and call a basic tool exposed by Graphiti's MCP server.

### 3.3. Future Enhancements (Post-MVP & Phase 2 - Core Focus)

*   **Advanced ADK Orchestration**: Implement LLM-driven dynamic routing in ADK for complex query decomposition and multi-tool usage.
*   **Sophisticated Temporal Queries**: Develop more complex queries leveraging Graphiti's bi-temporal model through Llama-Index or direct Cypher.
*   **Advanced Error Handling & Logging**: Implement robust error handling and logging across all components.
*   **Refined UI/UX**: Improve the Streamlit interface based on usage.
*   **Deeper MCP Integration**: Explore more complex interactions with external systems via MCP if use cases arise.

*(Out of Scope for initial phases: Multi-modal RAG, Federated Knowledge Graphs, Proactive Information Retrieval)*

## 4. Logical Dependency Chain (Focus on MVP - Phase 1)

1.  **Environment & Neo4j Setup**: Foundational. Cannot proceed without a working Python environment and Neo4j connection.
2.  **Graphiti Basic Ingestion**: Depends on Neo4j. Needed to have a graph to query.
3.  **Llama-Index KG Creation & Gemini Config**: Depends on Neo4j and a configured Gemini model. Needed to build the KG from documents and enable querying.
4.  **Llama-Index Basic Querying**: Depends on Llama-Index KG. Core RAG functionality.
5.  **Streamlit UI**: Depends on Llama-Index Querying. Provides user interaction.
6.  **Basic Hybrid Search**: Depends on Llama-Index KG with embeddings. Enhances MVP retrieval.

## 5. AI Pair Programmer Workflow

This project will be developed collaboratively with an AI Pair Programmer (Cascade). The following workflow will be adopted:

1.  **Master Build Plan**: 
    *   This PRD serves as the high-level input for creating a detailed Master Build Plan.
    *   The Master Build Plan will break down each phase and feature outlined in the "Development Roadmap" into main tasks.
2.  **Task Breakdown**: 
    *   Each main task in the Master Build Plan will be further broken down into smaller, manageable sub-tasks.
    *   These sub-tasks will be specific, actionable steps that can be implemented and tested incrementally.
3.  **Implementation**: 
    *   The AI Pair Programmer will assist in implementing these sub-tasks, generating code, configuring components, and integrating services.
4.  **Unit Testing**: 
    *   For each main task, the final sub-task will be to create comprehensive unit tests.
    *   These tests will verify that the functionality developed for the main task works correctly and integrates as expected within the project.
    *   The AI Pair Programmer will assist in writing these unit tests.
5.  **`buildprogress.md` - Living Document**:
    *   A file named `buildprogress.md` will be created and maintained in the `Project Documentation` directory.
    *   **Purpose**: 
        *   **Knowledge Repository**: Document important lessons learned, technical challenges encountered, solutions implemented, and any mistakes made to avoid repetition. This will include specific code snippets or configurations if relevant.
        *   **Current Project Status**: Provide a clear, up-to-date snapshot of where the project currently stands in relation to the Master Build Plan. This helps in understanding completed work and immediate next steps.
        *   **Context for AI**: Serve as a dynamic context source for the AI Pair Programmer (Cascade). By reviewing this document, the AI can quickly understand the current state of the project, recent developments, and any pertinent issues, facilitating more effective and context-aware collaboration.
    *   **Updates**: After the completion of each main task (including its unit tests), `buildprogress.md` will be updated by the AI Pair Programmer with:
        *   A summary of the completed task and its outcome.
        *   Key technical details, decisions made, and any significant learnings.
        *   The current status towards the next main task.
    *   **Detail Level**: Updates should be technically detailed enough to be useful for future reference and for providing clear context to the AI, avoiding generic or superficial entries.

## 6. Risks and Mitigations

*   **Complexity of Integration**: Integrating multiple advanced components (Graphiti, Llama-Index, Gemini, ADK, MCP) can lead to unexpected issues.
    *   **Mitigation**: Phased approach with incremental build and test cycles for each component integration. Focus on one integration point at a time.
*   **Learning Curve for New Technologies**: Some components (e.g., Graphiti-core, ADK, MCP) might have a steep learning curve.
    *   **Mitigation**: Allocate time for focused learning and experimentation with each new component. Start with simple examples and gradually increase complexity. Utilize documentation and community resources.
*   **Data Modeling for Temporal Graphs**: Designing effective Pydantic models and understanding the implications of Graphiti's bi-temporal model for specific use cases can be challenging.
    *   **Mitigation**: Start with simple entity models. Iteratively refine based on query needs and data ingestion patterns. Thoroughly test temporal query capabilities.
*   **LLM Prompt Engineering**: Getting optimal structured output and reasoning from Gemini Pro 2.5 will require careful prompt engineering.
    *   **Mitigation**: Iterative prompt development and testing. Utilize Gemini's "Thinking mode" to understand its reasoning process. Leverage Pydantic for enforcing output structure.
*   **Scope Creep for a Personal Project**: The sheer number of interesting features can lead to expanding scope beyond manageable limits for a single developer.
    *   **Mitigation**: Strictly adhere to the phased roadmap. Prioritize MVP features. Defer non-essential enhancements. The `buildprogress.md` can help track focus.

## 7. Appendix

*(To be populated with specific technical specifications, diagrams, or detailed API contracts as they are developed and if necessary for clarity during the build process.)*
