## Onboarding Instructions

Welcome to the `kev-new-graph-rag` project! To get started, follow these steps.

### 1. Understand the Architecture

First, read the main project overview document. It explains the goals, technologies, and high-level architecture of the system.
- **`@[./project_understanding.md]`**

### 2. Set Up Your Environment

1.  **Clone the repository.**
2.  **Install `uv`:** This project uses `uv` for package management and running scripts. Follow the official installation instructions.
3.  **Create your `.env` file:** Copy the `env.example` file to `.env` and fill in your credentials for Neo4j, Google Cloud, and any other required services.
4.  **Install dependencies:** Run `uv sync` in the project root to install all required Python packages.
5.  **Set up Google Cloud ADC:** Authenticate with Google Cloud by running `gcloud auth application-default login`.

### 3. Run the Application

The application consists of a backend server and a frontend UI, which must be run in separate terminals.

*   **To run the Backend Server:**
    ```powershell
    # From the project root
    uv run uvicorn src.backend.main_api:app --host 0.0.0.0 --port 8001 --reload --reload-dir src
    ```

*   **To run the Frontend UI:**
    ```powershell
    # From the project root
    uv run streamlit run src/app/main_ui.py
    ```

### 4. Explore the Codebase

Here are the most important parts of the codebase to familiarize yourself with:

*   **Backend API (`src/backend`):** The main FastAPI application. Look at `main_api.py` and the routers in `src/backend/routers/`.
*   **Frontend UI (`src/app`):** The Streamlit application. Start with `main_ui.py`.
*   **Ingestion Pipeline (`src/ingestion`):** The core of the data ingestion system. See `orchestrator.py` for how different pipelines are assembled and `steps.py` for the individual processing units.
*   **Query Orchestration (`src/graph_querying`):** The logic for the "Super Hybrid" search. See `super_hybrid_orchestrator.py`.
*   **Configuration (`src/utils/config_models.py`):** The Pydantic models that define and load all application configuration.
*   **Ontology (`src/ontology_templates/universal_ontology.py`):** The schema for the knowledge graph.
