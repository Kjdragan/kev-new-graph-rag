print("DEBUG: Script execution started - TOP OF FILE")
# src/graph_querying/graphiti_retriever.py

import os
from dotenv import load_dotenv
import yaml
import re

# Load environment variables from .env file
load_dotenv()




from datetime import datetime, timezone

from    llama_index.core.prompts import PromptTemplate
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core.indices.property_graph import TextToCypherRetriever




# Neo4j Credentials
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER") # Corrected convention
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Vertex AI Configuration
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")
GCP_REGION = os.getenv("GCP_LOCATION") # Using GCP_LOCATION from .env

# Custom Text-to-Cypher Prompt Template
CUSTOM_TEXT_TO_CYPHER_PROMPT_STR = """
Given an input question, convert it to a Cypher query.
You must only use the provided schema and not infer any node labels or relationship types not explicitly listed.
The Neo4j graph you are querying is managed by Graphiti and has specific conventions:

1.  **Node Labels:** Nodes always have a general ':Entity' label AND a specific entity type label. For example, a person node is queried as `(p:Entity:Person)`, an organization as `(o:Entity:Organization)`. Refer to the 'Node Labels' section in the schema below for available specific types.

2.  **Relationship Temporal Validity:** All relationships `[r:REL_TYPE]` must be filtered to include only those currently active. To do this, you MUST append the following conditions to every relationship in your Cypher query, using the provided `$current_datetime` parameter:
    `WHERE r.valid_at IS NOT NULL AND r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime) AND r.expired_at IS NULL`
    If a relationship variable is already part of a WHERE clause for other conditions, append these temporal conditions using AND. If a relationship is matched but has no other specific conditions, you must still add this temporal WHERE clause.

3.  **Property Names:** Use the exact property names as defined in the 'Node Properties' and 'Relationship Properties' sections of the schema.

4.  **Mapping Question Entities to Cypher:**
    *   When the question mentions a specific entity (e.g., a person's name like "Alice", an organization name), you MUST try to find this entity in the graph using its properties. For example, if the schema defines a `Person` node with a `person_name` property, a question about "Alice" should translate to a Cypher clause like `MATCH (p:Entity:Person) WHERE p.person_name = 'Alice'` or by passing 'Alice' as a parameter if appropriate (see next point).
    *   When the question asks about a general category like "projects", "papers", "companies", you should identify the most relevant node type(s) from the provided schema (e.g., `Content`, `Resource`, `Technology`, `Organization`) to represent this category.
    *   Cypher parameters (e.g., `$some_value`) should ONLY be used if their value is directly and explicitly available in the user's question or if a parameter is explicitly provided to you (like `$current_datetime`). DO NOT invent parameters for concepts not directly extractable from the question. For instance, if the question is "What is Alice working on?", do not create a parameter like `$project_name` unless "project_name" is part of the question. Instead, query for relationships connected to the 'Alice' node.

**Schema:**
---------------------
{schema}
---------------------

**Instructions:**
-   Generate a Cypher query.
-   The Cypher query MUST be plain text. DO NOT include any markdown formatting such as ```cypher or ```. The query should start directly with a Cypher keyword like MATCH, OPTIONAL MATCH, etc.
-   Ensure all matched relationships `[r:REL_TYPE]` include the temporal validity WHERE clause mentioned in point 2.
-   Ensure all matched nodes use the dual-label convention mentioned in point 1 (e.g., `(n:Entity:SpecificType)`).
-   Use the `$current_datetime` parameter as provided for temporal filtering. The value for `$current_datetime` will be an ISO 8601 timestamp string (e.g., "2025-06-14T15:30:12-05:00").
-   Pay close attention to point 4 under "Graphiti Conventions" regarding how to map entities from the question to Cypher and when to use parameters.
-   The output MUST be a valid Cypher query string. Do not return placeholders like "{cypher_query}" or any other template variables.

**Question:** {query_str}
**Cypher Query:**
"""

custom_text_to_cypher_prompt = PromptTemplate(CUSTOM_TEXT_TO_CYPHER_PROMPT_STR)

class SanitizedTextToCypherRetriever(TextToCypherRetriever):
    """A TextToCypherRetriever that cleans markdown from the generated Cypher query."""
    def _parse_generated_cypher(self, cypher_query: str) -> str:
        # Overrides the base method to clean the Cypher query string
        cleaned_query = cypher_query
        if isinstance(cypher_query, str):
            # Remove ```cypher prefix (case-insensitive) and leading/trailing whitespace
            cleaned_query = re.sub(r"^\s*```cypher\s*", "", cleaned_query, flags=re.IGNORECASE)
            # Remove ``` suffix and leading/trailing whitespace
            cleaned_query = re.sub(r"\s*```\s*$", "", cleaned_query)
            # Also handle cases where it might just be ``` without 'cypher' (e.g. from a faulty LLM response)
            cleaned_query = re.sub(r"^\s*```\s*", "", cleaned_query).strip()

        # After our cleaning, pass to the original validator if it exists
        # The base class's _parse_generated_cypher calls self.cypher_validator(cleaned_query) or returns cleaned_query
        print(f"DEBUG: Cleaned Cypher Query: {cleaned_query}") # Log the cleaned query
        if self.cypher_validator is not None:
            return self.cypher_validator(cleaned_query)
        return cleaned_query


def get_graphiti_text2cypher_retriever():
    # Load model_id from config.yaml
    config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        llm_model_name = config['gemini']['models']['pro']['model_id']
        print(f"Using LLM model from config: {llm_model_name}")
    except Exception as e:
        print(f"Error loading model_id from config.yaml: {e}. Falling back to default.")
        llm_model_name = "gemini-1.5-flash" # Fallback, though this was the problematic one
    """
    Initializes and returns a TextToCypherRetriever configured for Graphiti using Vertex AI.
    """
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, GCP_PROJECT_ID, GCP_REGION]):
        raise ValueError("Missing necessary environment variables for Neo4j or Google Cloud Vertex AI.")

    graph_store = Neo4jPropertyGraphStore(
        username=NEO4J_USER,
        password=NEO4J_PASSWORD,
        url=NEO4J_URI,
        database=NEO4J_DATABASE,
    )

    # Configure the LLM to use Vertex AI via vertexai_config
    llm = GoogleGenAI(
        model_name=llm_model_name, # Parameter name is model_name for GoogleGenAI
        vertexai_config={
            "project": GCP_PROJECT_ID,
            "location": GCP_REGION,
        }
    )

    retriever = SanitizedTextToCypherRetriever(
        graph_store=graph_store,
        llm=llm,
        text_to_cypher_template=custom_text_to_cypher_prompt,
        verbose=True
    )
    return retriever

def execute_graphiti_query(retriever: TextToCypherRetriever, query_str: str):
    """
    Executes a natural language query using the Graphiti-configured retriever.
    Handles passing the $current_datetime parameter.
    """
    current_dt_iso = datetime.now(timezone.utc).isoformat()

    print(f"Attempting to execute query: '{query_str}'")
    print(f"Using current_datetime: {current_dt_iso}")

    # The key challenge is passing the `current_datetime` parameter.
    # The `TextToCypherRetriever` does not directly accept `params` for its `retrieve` method.
    # We are attempting to set a temporary attribute on the graph_store instance.
    # This needs to be verified during the test run.
    original_params = getattr(retriever._graph_store, 'cypher_query_params', {})
    try:
        retriever._graph_store.cypher_query_params = {
            **original_params,
            "current_datetime": current_dt_iso
        }
        nodes = retriever.retrieve(query_str)
        return nodes
    except Exception as e:
        print(f"Error during query execution: {e}")
        print("This might be due to $current_datetime not being passed correctly.")
        return []
    finally:
        # Always reset the params to avoid side effects
        retriever._graph_store.cypher_query_params = original_params

if __name__ == '__main__':
    print("DEBUG: Entering main block...")
    print("Starting Graphiti Retriever example...")
    try:
        retriever = get_graphiti_text2cypher_retriever()
        nl_query = "What projects is Alice working on?"

        print(f"Executing NL Query: {nl_query}")
        results = execute_graphiti_query(retriever, nl_query)

        if results:
            print("Query Results:")
            for node_with_score in results:
                print(f"  Node: {node_with_score.node.properties}")
                print(f"  Score: {node_with_score.score}")
        else:
            print("No results returned or an error occurred.")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
