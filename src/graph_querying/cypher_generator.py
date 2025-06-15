"""
Handles the generation of Cypher queries from natural language using Google Gemini LLM
with structured output.
"""
import os
import json
from google import genai # Main SDK import
from google.genai.types import GenerateContentConfig, HttpOptions # Specific types, using GenerateContentConfig as per example
import dotenv
from dotenv import load_dotenv

# genai.types.GenerationConfig will be used for specifying response_mime_type
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional

from src.graph_querying.schema_utils import get_ontology_schema_string



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

async def generate_cypher_query(
    natural_language_query: str,
    ontology_schema: Optional[str] = None,
    gemini_model_name: str = "gemini-2.5-pro-preview-06-05", # Using the correct model from config.yaml
    # In a real scenario, you might pass a Graphiti SearchResults object here for context
    # search_context: Optional[Any] = None
) -> CypherQueryResult:
    """
    Generates a Cypher query from a natural language query using Gemini LLM.

    Args:
        natural_language_query: The user's query in natural language.
        ontology_schema: The ontology schema string. If None, it will be generated.
        gemini_model_name: The name of the Gemini model to use.
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
    # Note: For production, consider more robust error handling and model configuration (e.g., safety settings)
    effective_model_name = gemini_model_name
    # When using GOOGLE_GENAI_USE_VERTEXAI=True, the SDK should handle routing.
    # The model name is typically the direct ID like 'gemini-2.5-pro-preview-06-05'.

    try:
        # Instantiate the client with HttpOptions, as per the new example.
        # It will pick up env vars for Vertex AI config if GOOGLE_GENAI_USE_VERTEXAI is True.
        client = genai.Client(http_options=HttpOptions(api_version="v1"))

        # Configure for JSON output using GenerateContentConfig
        config = GenerateContentConfig(
            response_mime_type="application/json" # Assuming this is a valid parameter for GenerateContentConfig
        )

        # Use the client.aio.models.generate_content pattern for async calls.
        response = await client.aio.models.generate_content(
            model=effective_model_name, # This is the model ID string
            contents=prompt,
            config=config # Corrected keyword argument
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
        result = await generate_cypher_query(test_nl_query)
        print("\nSuccessfully generated Cypher query:")
        print(f"  Query: {result.cypher_query}")
        print(f"  Parameters: {result.parameters}")
        print(f"  Explanation: {result.explanation}")
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
