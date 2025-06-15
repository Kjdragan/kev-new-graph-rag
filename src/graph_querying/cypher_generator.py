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

# genai.types.GenerationConfig will be used for specifying response_mime_type
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional

from src.graph_querying.schema_utils import get_ontology_schema_string
from src.graph_querying.neo4j_executor import execute_cypher_query, Neo4jConnectionError, Neo4jQueryError



# Define the Pydantic model for structured LLM output
class CypherQueryResult(BaseModel):
    """Pydantic model for the structured output of the Cypher generation LLM call."""
    cypher_query: str = Field(..., description="The generated Cypher query string.")
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

async def generate_cypher_query(
    natural_language_query: str,
    ontology_schema: Optional[str] = None,
    model_config_type: str = "flash", # Specifies 'flash' or 'pro' from config.yaml
    # In a real scenario, you might pass a Graphiti SearchResults object here for context
    # search_context: Optional[Any] = None
) -> CypherQueryResult:
    """
    Generates a Cypher query from a natural language query using Gemini LLM.

    Args:
        natural_language_query: The user's query in natural language.
        ontology_schema: The ontology schema string. If None, it will be generated.
        model_config_type: The key (e.g., 'flash', 'pro') from config.yaml to use for model ID and budget.
        # search_context: Optional context from a preliminary Graphiti search.

    Returns:
        A CypherQueryResult object containing the Cypher query and parameters.

    Raises:
        CypherGenerationError: If the LLM fails to generate a valid structured response.
    """
    if ontology_schema is None:
        print("Ontology schema not provided, generating it now...")
        ontology_schema = get_ontology_schema_string()
        if "ERROR:" in ontology_schema: # Basic check if schema generation failed
            raise CypherGenerationError(f"Failed to generate ontology schema: {ontology_schema}")

    # Construct the prompt for the Gemini LLM
    prompt_parts = [
        "You are an expert Cypher query generator for a Neo4j graph database.",
        "Your task is to translate the user's natural language query into an executable Cypher query, "
        "based on the provided ontology schema.",
        "\n## Ontology Schema:",
        ontology_schema,
        "\n## Instructions:",
        "1. Generate a Cypher query that accurately reflects the user's intent.",
        "2. Use the property names and relationship types exactly as defined in the schema.",
        "3. For temporal filtering (e.g., finding active relationships at the current time), use the parameter `$current_datetime`. "
        "   The application will provide the actual datetime value for this parameter at runtime.",
        "   A typical condition for an active relationship 'r' is: "
        "   `r.valid_at <= $current_datetime AND (r.invalid_at IS NULL OR r.invalid_at > $current_datetime)`.",
        "4. If the user's query implies filtering by specific dates or date ranges other than 'now', incorporate those specific dates directly or as parameters.",
        "5. Return the Cypher query and any necessary parameters (including `$current_datetime` if used) in the specified JSON format.",
        "6. Provide a brief explanation of how the query addresses the user's request.",
        "\n## User's Natural Language Query:",
        natural_language_query,
        "\n## Required Output Format:",
        "Return a single JSON object matching the Pydantic model `CypherQueryResult`:",
        json.dumps(CypherQueryResult.model_json_schema(), indent=2), # Convert schema dict to JSON string
    ]

    prompt = "\n".join(prompt_parts)

    # Initialize the Gemini model
    # Load model_id and thinking_budget from config.yaml based on gemini_model_name
    # This assumes gemini_model_name is a key like 'pro' or 'flash' if we want to use config.yaml directly
    # For now, we are passing the full model_id, so we need a way to map back or adjust loading
    # Let's adjust the logic: if gemini_model_name is a full ID, we try to find its type ('pro' or 'flash')
    # or we directly use the passed gemini_model_name and fetch its specific budget if defined.
    # For simplicity in this step, we'll assume `gemini_model_name` is used to fetch budget if it's a key in config.
    # However, the current call from main passes the full ID. So, we need to adjust how `load_config` is used or what `gemini_model_name` signifies.

    # Let's refine: The `generate_cypher_query` function takes `gemini_model_name` which IS the model_id.
    # We need to determine if this model_id corresponds to 'pro' or 'flash' to get its budget from config.
    # This is a bit circular. A better approach: `main` decides 'pro' or 'flash', loads config, then passes model_id and budget.

    # For now, to make progress and test with the flash model's budget:
    # We know `main` is calling with flash_model_id. We'll hardcode fetching 'flash' budget for this test.
    # Load model_id and thinking_budget from config.yaml based on model_config_type
    effective_model_name, thinking_budget = load_config(model_config_type)
    print(f"Using model configuration: '{model_config_type}' (ID: {effective_model_name}, Budget: {thinking_budget})")

    try:
        client = genai.Client(http_options=HttpOptions(api_version="v1"))

        gen_config_params = {"response_mime_type": "application/json"}
        if thinking_budget > 0:
            print(f"Applying thinking_budget: {thinking_budget} for model {effective_model_name}")
            gen_config_params["thinking_config"] = ThinkingConfig(budget=thinking_budget)
        
        config = GenerateContentConfig(**gen_config_params)

        response = await client.aio.models.generate_content(
            model=effective_model_name, # Use the model_id loaded from config
            contents=prompt,
            config=config
        )
    except Exception as e:
        # Add more specific error logging if possible
        # For example, check if e has attributes like e.response for more details
        error_message = f"Error calling Gemini API (via google.genai Client): {e}"
        # if hasattr(e, 'response') and e.response:
        #     error_message += f" | Response: {e.response}"
        print(f"DEBUG: Prompt sent to LLM:\n{prompt[:1000]}...\n") # Log first 1k chars of prompt
        raise CypherGenerationError(error_message)

    try:
        # The response object from client.models.generate_content_async should have a .text attribute
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


    test_nl_query = "What organizations are developing AI technologies that were announced after January 2023?"

    print(f"\nNatural Language Query: {test_nl_query}")

    try:
        # Use 'flash' model type from config.yaml, which includes its thinking_budget
        result = await generate_cypher_query(test_nl_query, model_config_type="flash")
        print("\nSuccessfully generated Cypher query:")
        print(f"  Query: {result.cypher_query}")
        print(f"  Parameters: {result.parameters}")
        print(f"  Explanation: {result.explanation}")

        # Now, execute the generated query
        if result.cypher_query:
            print("\nAttempting to execute generated Cypher query...")
            try:
                query_execution_results = execute_cypher_query(
                    query=result.cypher_query,
                    parameters=result.parameters
                    # database_name can be specified here if needed, e.g., os.getenv("NEO4J_DATABASE_MAIN")
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
