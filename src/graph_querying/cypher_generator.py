"""
Handles the generation of Cypher queries from natural language using Google Gemini LLM
with structured output.
"""
import os
import json
from google import genai # Main SDK import
from google.genai.types import GenerateContentConfig, HttpOptions, ThinkingConfig # Specific types, including ThinkingConfig
import dotenv
from dotenv import load_dotenv
from pathlib import Path # Added to resolve NameError
import yaml # Added to resolve NameError

# genai.types.GenerationConfig will be used for specifying response_mime_type
from pydantic import BaseModel, Field, ValidationError, AliasChoices
from typing import Dict, Any, Optional

from src.graph_querying.schema_utils import get_ontology_schema_string
from src.graph_querying.neo4j_executor import execute_cypher_query, Neo4jConnectionError, Neo4jQueryError



# Define the Pydantic model for structured LLM output
class CypherQueryResult(BaseModel):
    """Pydantic model for the structured output of the Cypher generation LLM call."""
    cypher_query: str = Field(..., validation_alias=AliasChoices('cypher_query', 'query', 'cypher'), description="The generated Cypher query string.")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="A dictionary of parameters to be used with the Cypher query. "
                    "Must include '$current_datetime' if temporal filtering is needed."
    )
    explanation: Optional[str] = Field(None, description="A brief explanation of the generated query.")

class CypherGenerationError(Exception):
    """Custom exception for errors during Cypher generation."""
    pass

def load_config(model_type: str = "pro") -> tuple[str, int]:
    """Loads model ID and thinking budget from config.yaml for the given model type."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"config.yaml not found at {config_path}")

    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)

    try:
        model_config = config_data['gemini']['models'][model_type]
        model_id = model_config['model_id']
        thinking_budget = model_config.get('thinking_budget', 0) # Default to 0 if not specified
        return model_id, int(thinking_budget)
    except KeyError as e:
        raise KeyError(f"Could not find configuration for model_type '{model_type}' in config.yaml: {e}")
    except ValueError as e:
        raise ValueError(f"Invalid thinking_budget for model_type '{model_type}' in config.yaml: {e}")

# Define the canonical mapping of (SourceNode, TargetNode) -> [RELATIONSHIP_TYPES_IN_NEO4J]
# IMPORTANT: Relationship types here MUST match the exact strings used in Neo4j by Graphiti.
# Assuming Pydantic class names (CamelCase) are converted to UPPER_SNAKE_CASE for Neo4j.
# User should verify and adjust this map based on their actual Graphiti ingestion naming.
# Maps (Source, Target) to the 'name' property value on the RELATES_TO relationship.
# These are derived from the Universal Ontology relationship classes.
EDGE_TYPE_MAP = {
    ('Person', 'Event'): ['PARTICIPATES_IN'],
    ('Organization', 'Event'): ['PARTICIPATES_IN'],
    ('Person', 'Organization'): ['PARTICIPATES_IN'],
    ('Organization', 'Location'): ['LOCATED_IN'],
    ('Event', 'Location'): ['LOCATED_IN'],
    ('Person', 'Location'): ['LOCATED_IN'],
    ('Resource', 'Location'): ['LOCATED_IN'],
    ('Technology', 'Location'): ['LOCATED_IN'],
    ('Person', 'Content'): ['HAS_CREATOR', 'CREATES'],
    ('Organization', 'Content'): ['HAS_CREATOR', 'CREATES'],
    ('Person', 'Technology'): ['HAS_CREATOR', 'CREATES'],
    ('Organization', 'Technology'): ['HAS_CREATOR', 'CREATES'],
    ('Organization', 'Resource'): ['HAS_CREATOR', 'CREATES'],
    ('Person', 'Agreement'): ['HAS_CREATOR', 'CREATES'],
    ('Organization', 'Agreement'): ['HAS_CREATOR', 'CREATES'],
    ('Person', 'Event'): ['HAS_CREATOR', 'CREATES'],
    ('Person', 'Technology'): ['USES'],
    ('Organization', 'Technology'): ['USES'],
    ('Technology', 'Resource'): ['USES'],
    ('Organization', 'Resource'): ['USES'],
    ('Person', 'Resource'): ['USES'],
    ('Event', 'Technology'): ['USES'],
    ('Person', 'Person'): ['SUPPORTS'],
    ('Organization', 'Person'): ['SUPPORTS'],
    ('Person', 'Organization'): ['SUPPORTS'],
    ('Organization', 'Organization'): ['SUPPORTS'],
    ('Content', 'Topic'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Person'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Organization'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Event'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Technology'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Resource'): ['DISCUSSES', 'MENTIONS'],
    ('Content', 'Location'): ['DISCUSSES', 'MENTIONS'],
    ('Event', 'Topic'): ['DISCUSSES', 'MENTIONS'],
    ('Person', 'Topic'): ['DISCUSSES', 'MENTIONS'],
    ('Person', 'Organization'): ['CONTROLS'],
    ('Organization', 'Organization'): ['CONTROLS'],
    ('Organization', 'Resource'): ['CONTROLS'],
    ('Person', 'Resource'): ['CONTROLS'],
    ('Organization', 'Location'): ['CONTROLS'],
    ('Person', 'Person'): ['INFLUENCES'],
    ('Organization', 'Person'): ['INFLUENCES'],
    ('Event', 'Person'): ['INFLUENCES'],
    ('Technology', 'Organization'): ['INFLUENCES'],
    ('Topic', 'Person'): ['INFLUENCES'],
    ('Topic', 'Organization'): ['INFLUENCES'],
    ('Content', 'Person'): ['INFLUENCES'],
    ('Content', 'Organization'): ['INFLUENCES'],
}

async def generate_cypher_query(
    nl_query: str,
    ontology_schema: str,
    model_config_key: str = 'flash'
) -> Optional[CypherQueryResult]:
    """Generates a Cypher query from a natural language query using a Gemini model.

    Args:
        nl_query: The natural language query.
        ontology_schema: A string representation of the graph ontology.
        model_config_key: The key for the model configuration in config.yaml.

    Returns:
        A CypherQueryResult object or None if an error occurs.
    """
    if "ERROR:" in ontology_schema:
        raise CypherGenerationError(f"Failed to generate ontology schema: {ontology_schema}")

    edge_map_str = "\n".join(f"- ({source}, {target}) -> {rels}" for (source, target), rels in EDGE_TYPE_MAP.items())

    system_prompt = f"""You are an expert Neo4j Cypher query writer. Your task is to convert a natural language question into a Cypher query based on a provided graph schema. Follow these rules strictly.

### CRITICAL RULES:
1.  **Relationship Types**: The graph has only TWO relationship types: `RELATES_TO` and `MENTIONS`. You MUST use one of these.
2.  **Relationship `name` Property**: To specify the *meaning* of a relationship (e.g., who created something), you MUST filter on the `name` property of the relationship. For example: `MATCH (a)-[r:RELATES_TO]->(b) WHERE r.name = 'CREATES'`.
3.  **Node and Property Names**: You MUST use the exact node labels (e.g., `Organization`, `Technology`) and property names (e.g., `organization_name`, `tech_name`) provided in the schema. DO NOT invent or assume property names.
4.  **Temporal Filtering**: For queries involving dates, use the `$current_datetime` parameter for the present moment. A relationship is considered current if `r.valid_at <= $current_datetime` AND (`r.invalid_at IS NULL` OR `r.invalid_at > $current_datetime`).

### PERFECT QUERY EXAMPLE:
*   **Natural Language Question**: "Who created GPT-4?"
*   **Correct Cypher Query and Parameters**:
    ```json
    {{
        "cypher_query": "MATCH (creator:Organization)-[r:RELATES_TO]->(tech:Technology) WHERE r.name = 'CREATES' AND tech.tech_name = $tech_name RETURN creator.organization_name",
        "parameters": {{
            "tech_name": "GPT-4"
        }},
        "explanation": "This query finds an Organization that has a 'CREATES' relationship with a Technology named 'GPT-4' and returns the organization's name."
    }}
    ```

### YOUR TASK
Here is the graph schema:
{ontology_schema}

This map shows the valid `name` values for a `RELATES_TO` relationship between pairs of node labels.
{edge_map_str}

Based on the schema and rules, generate a Cypher query and parameters for the following natural language question.
User Query: {nl_query}

You MUST provide your response as a single, valid JSON object that conforms to the following Pydantic model. Do not include any text or markdown formatting before or after the JSON object.

Here is the Pydantic model for your reference:
```python
class CypherQueryResult(BaseModel):
    cypher_query: str
    parameters: Dict[str, Any]
    explanation: str
```
"""

    effective_model_name, thinking_budget = load_config(model_config_key)
    print(f"Using model configuration: '{model_config_key}' (ID: {effective_model_name}, Budget: {thinking_budget})")

    try:
        client = genai.Client(http_options=HttpOptions(api_version="v1"))

        gen_config_params = {"response_mime_type": "application/json"}
        if thinking_budget > 0:
            print(f"Applying thinking_budget: {thinking_budget} for model {effective_model_name}")
            gen_config_params["thinking_config"] = ThinkingConfig(thinking_budget=thinking_budget)
        
        config = GenerateContentConfig(**gen_config_params)

        response = await client.aio.models.generate_content(
            model=effective_model_name,
            contents=system_prompt,
            config=config
        )
    except Exception as e:
        error_message = f"Error calling Gemini API (via google.genai Client): {e}"
        print(f"DEBUG: Prompt sent to LLM:\n{system_prompt[:1500]}...\n")
        raise CypherGenerationError(error_message)

    try:
        if not response.text:
             raise CypherGenerationError("Gemini API (via google.genai Client) returned an empty response.")

        query_result = CypherQueryResult.model_validate_json(response.text)
        return query_result
    except ValidationError as ve:
        error_details = ve.errors()
        raise CypherGenerationError(
            f"Failed to validate LLM response against Pydantic model. Errors: {error_details}\nRaw Response: {response.text}"
        )
    except Exception as e:
        raise CypherGenerationError(f"Error processing LLM response: {e}\nRaw Response: {response.text}")

# Example usage (can be run with `uv run python -m src.graph_querying.cypher_generator`)
async def main():
    print("Testing Cypher Query Generation with google-genai SDK...")

    # Load environment variables for the test run
    GOOGLE_GENAI_USE_VERTEXAI = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False").lower() == "true"
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION")

    if GOOGLE_GENAI_USE_VERTEXAI:
        print(f"Attempting to use Vertex AI via google-genai SDK (Project: {GOOGLE_CLOUD_PROJECT}, Location: {GOOGLE_CLOUD_LOCATION})")
        if not GOOGLE_CLOUD_PROJECT or not GOOGLE_CLOUD_LOCATION:
            print("ERROR: GOOGLE_GENAI_USE_VERTEXAI is True, but GOOGLE_CLOUD_PROJECT or GOOGLE_CLOUD_LOCATION is not set. Aborting.")
            return
    else:
        print("Attempting to use standard Gemini API via google-genai SDK (using GOOGLE_API_KEY if set).")
        if not os.getenv("GOOGLE_API_KEY"):
            print("WARNING: GOOGLE_API_KEY not set and not using Vertex AI. Calls may fail if model is not public.")


    test_nl_query = "Who created GPT-4?"

    print(f"\nNatural Language Query: {test_nl_query}")

    try:
        print("Generating ontology schema for prompt...")
        ontology_schema = get_ontology_schema_string()
        
        # Use 'flash' model type from config.yaml, which includes its thinking_budget
        result = await generate_cypher_query(
            nl_query=test_nl_query,
            ontology_schema=ontology_schema,
            model_config_key="flash",
        )
        print("\nSuccessfully generated Cypher query:")
        print(f"  Query: {result.cypher_query}")
        print(f"  Parameters: {result.parameters}")
        print(f"  Explanation: {result.explanation}")

        # Now, execute the generated query
        if result.cypher_query:
            print("\nAttempting to execute generated Cypher query...")
            try:
                # Get the current time in UTC and format it as ISO 8601 string
                from datetime import datetime, timezone
                now_utc = datetime.now(timezone.utc).isoformat()

                # IMPORTANT: Override any placeholder for current_datetime with the actual current time.
                # The LLM is instructed to use the parameter '$current_datetime', so we ensure it's set correctly.
                if 'current_datetime' in result.parameters:
                    print(f"Replacing placeholder `current_datetime` with actual value: {now_utc}")
                    result.parameters['current_datetime'] = now_utc

                query_execution_results = execute_cypher_query(
                    query=result.cypher_query,
                    parameters=result.parameters
                )
                print("\nSuccessfully executed Cypher query.")
                print(f"Results ({len(query_execution_results)} records):")
                for i, record in enumerate(query_execution_results):
                    print(f"  Record {i+1}: {record}")
                    if i >= 4: # Print max 5 records for brevity in testing
                        print(f"  ... (and {len(query_execution_results) - 5} more records)")
                        break
            except Neo4jConnectionError as ne:
                print(f"\nNeo4j Connection Error: {ne}")
                print("Please ensure Neo4j is running and .env variables (NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD) are correctly set.")
            except Neo4jQueryError as nqe:
                print(f"\nNeo4j Query Error: {nqe}")
            except Exception as exec_e:
                print(f"\nAn unexpected error occurred during query execution: {exec_e}")
        else:
            print("\nSkipping query execution as no Cypher query was generated.")

    except CypherGenerationError as e:
        print(f"\nError generating Cypher query: {e}")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    import asyncio
    # For asyncio in scripts, it's common to use asyncio.run()
    # However, if running in an environment that already has an event loop (like Jupyter),
    # this might need adjustment.
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if " asyncio.run() cannot be called from a running event loop" in str(e):
            print("Skipping main() in a running event loop environment (e.g., Jupyter Notebook).")
        else:
            raise
