## Onboarding Instructions

To get up to speed on this project, review the following files and directories. They provide essential context on the project's goals, architecture, configuration, and current implementation.

### Core Project & Framework Documentation
- **Frameworks:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\workingwithgenai.md]` - Explains how to use the `google-genai` SDK with ADC.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\understanding_graphiti_search.md]` - Details the principles of Graphiti-native search.
- **Overall Project:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\Project Documentation\project_understanding.md]` - High-level overview of the project goals and architecture.

### Project-Specific Implementation & Configuration
- **Configuration:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\.env]` - Environment variables for Neo4j, Google Cloud, etc.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\config.yaml]` - Application-level configuration, including model IDs.
- **Backend Code:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\src\backend]` - The main FastAPI application, including all routers (chat, graph, ingest).
- **Querying & Ingestion:**
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\src\graph_querying\test_hybrid_search.py]` - Example usage of the `GraphitiNativeSearcher`.
  - `@[c:\Users\kevin\repos\kev-new-graph-rag\scripts\ingest_gdrive_documents.py]` - The original manual ingestion script (Note: this is being replaced by the UI-driven workflow).

*This list is dynamic and should be updated as the project evolves and manual scripts are replaced by modular, UI-driven components.*
