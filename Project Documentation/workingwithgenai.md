# Working with the google-genai SDK for Vertex AI

This document outlines the best practices, configuration, and lessons learned
for using the `google-genai` Python SDK to interact with Google Gemini models
via Vertex AI within the `kev-new-graph-rag` project.

## 1. SDK Selection and Core Import

- **SDK**: The project exclusively uses the `google-genai` PyPI package. This is
  the unified SDK for Google's Gemini models, supporting both direct Gemini API
  access and integration with Vertex AI.
  - Installation: `uv add google-genai`
- **Core Import**: The ONLY correct way to import the SDK is:
  ```python
  from google import genai
  ```
- **Deprecated SDKs**: Avoid using the older `google-generativeai` package or
  relying solely on `google-cloud-aiplatform` for direct Gemini model
  interactions, as `google-genai` provides the preferred unified interface.

## 2. Configuring for Vertex AI with Application Default Credentials (ADC)

The `google-genai` SDK is designed to seamlessly integrate with Vertex AI and
use Application Default Credentials (ADC) when specific environment variables
are set. No manual API key configuration is needed in the code when using this
method.

- **Required Environment Variables** (typically set in a `.env` file and loaded
  by `python-dotenv`):
  - `GOOGLE_GENAI_USE_VERTEXAI=True`: This is the critical flag that tells the
    SDK to target Vertex AI.
  - `GOOGLE_CLOUD_PROJECT="your-gcp-project-id"`: Specifies your Google Cloud
    Project ID.
  - `GOOGLE_CLOUD_LOCATION="your-gcp-region"`: Specifies the GCP region for
    Vertex AI services (e.g., `us-central1`).

- **How it Works**: When these environment variables are present and
  `from google import genai` is used, the SDK automatically handles
  authentication with Vertex AI using the credentials available in your
  environment (e.g., from `gcloud auth application-default login`).
- **ADC vs. API Keys**: This ADC method is the standard and recommended approach
  for application-based authentication on Google Cloud. It is more secure and
  manageable than embedding API keys directly into application code or
  configuration files. While API keys can be used with the Gemini API directly
  (not via Vertex AI, typically by setting `GOOGLE_API_KEY`), the ADC approach
  via Vertex AI is preferred for this project for consistency with GCP best
  practices and other services.

## 3. Asynchronous API Calls with `genai.Client` (Current Best Practice)

For asynchronous operations, such as generating content within an `async`
function, the recommended pattern involves using `genai.Client` configured with
`HttpOptions` and accessing the asynchronous methods via `client.aio.models`.

- **Necessary Imports**:
  ```python
  from google import genai
  from google.genai.types import GenerateContentConfig, HttpOptions
  ```

- **Client Instantiation**:
  ```python
  client = genai.Client(http_options=HttpOptions(api_version="v1"))
  ```
  _Note: The `api_version` might need adjustment based on future SDK updates or
  specific model requirements._

- **Making Asynchronous Calls**:
  ```python
  # Assuming 'effective_model_name' is sourced from config.yaml (e.g., "gemini-2.5-pro")
  # Assuming 'prompt' is the constructed input string/list for the LLM

  # Assuming 'prompt' is the constructed input string/list for the LLM

  # Use GenerateContentConfig as per the latest examples
  content_config = GenerateContentConfig(
      response_mime_type="application/json" # For structured JSON output.
                                         # The example used response_modalities=["TEXT"],
                                         # so this assumes response_mime_type is also valid here.
  )

  response = await client.aio.models.generate_content(
      model=effective_model_name, # The model ID string
      contents=prompt,
      config=content_config # Note: The keyword is 'config' here
  )

  # Process response (e.g., response.text, or response.parts if more complex)
  ```

## 4. Model Naming and Configuration

- **Model IDs**: The project now uses the Generally Available (GA) Gemini 2.5
  models. Specific model IDs (`gemini-2.5-pro` and `gemini-2.5-flash`) should be
  managed in the project's `config.yaml` file and loaded dynamically.
  - **`gemini-2.5-pro`**: Strongest model for quality, code, and complex
    reasoning. Features a 1M token context window.
  - **`gemini-2.5-flash`**: Best for balancing reasoning and speed. Also
    features a 1M token context window.
- **Structured Output**: To receive JSON-formatted output from the LLM, use
  `GenerateContentConfig(response_mime_type="application/json")` for structured
  output (note the class name change based on examples). The LLM prompt must
  also instruct the model to generate JSON.

- **Thinking Budget (for applicable models like Flash)**:
  - To enable and control the "thinking" budget for models that support it
    (e.g., `gemini-2.5-flash-preview-05-20`), use the `ThinkingConfig` type from
    `google.genai.types`.
  - The budget is specified using the `thinking_budget` parameter within
    `ThinkingConfig`.
  - This `ThinkingConfig` instance is then passed to the `thinking_config`
    parameter of `GenerateContentConfig`.
  - Example:
    ```python
    from google.genai.types import GenerateContentConfig, ThinkingConfig

    # Assuming 'thinking_budget_value' is loaded from config.yaml (e.g., 1024)
    # Assuming 'effective_model_name' is the model ID (e.g., 'gemini-2.5-flash-preview-05-20')

    gen_config_params = {"response_mime_type": "application/json"}
    if thinking_budget_value > 0:
        print(f"Applying thinking_budget: {thinking_budget_value} for model {effective_model_name}")
        # Correct instantiation:
        gen_config_params["thinking_config"] = ThinkingConfig(thinking_budget=thinking_budget_value)

    content_config = GenerateContentConfig(**gen_config_params)

    # Then use 'content_config' in the client.aio.models.generate_content call:
    # response = await client.aio.models.generate_content(
    #     model=effective_model_name,
    #     contents=prompt,
    #     config=content_config
    # )
    ```
  - A `thinking_budget` of `0` effectively turns off the thinking feature for
    that call.
  - **Important**: Ensure you are using the correct parameter name
    (`thinking_budget`) within the `ThinkingConfig` constructor. Initial
    attempts using `budget` or setting an attribute dynamically after
    instantiation (`tc.budget = ...`) will result in errors.

## 5. Evolution of Understanding & Lessons Learned (Troubleshooting Journey)

### Model Availability in Vertex AI

- **Symptom**: API calls to `client.aio.models.generate_content` might fail with
  a `404 NOT_FOUND` error, with a message like:
  `Publisher Model 'projects/YOUR_PROJECT/locations/YOUR_LOCATION/publishers/google/models/MODEL_ID' not found.`
- **Cause**: This typically means the specified `MODEL_ID` is not available for
  your Google Cloud Project in the specified location. With the move away from
  preview models, this is less likely, but can still occur with regional
  availability differences.
- **Troubleshooting**:
  1. Verify the model ID in your `config.yaml` or code against the available
     models in the Google Cloud Console for Vertex AI in your project and
     region.
  2. Test with a generally available model (e.g., a "flash" variant like
     `gemini-2.5-flash-preview-05-20`) to confirm the rest of the SDK
     integration and authentication is working. If the flash model works, the
     issue is likely specific to the originally requested model's availability.
  3. Ensure the model is explicitly enabled for your project if it's a preview
     or restricted model.
- **Example**: In this project, initial calls with preview model versions failed
  with a 404 error. Switching to the GA versions (`gemini-2.5-pro`,
  `gemini-2.5-flash`) resolved these issues, confirming that using the latest GA
  models is the correct approach.

Our path to the current best practice involved several iterations and
troubleshooting steps:

1. **Initial `genai.configure()` Attempts**: Early use of `genai.configure()`
   was incorrect as this function is not part of the `google-genai` client
   library's standard flow when using ADC with Vertex AI, or it has been
   deprecated/changed in the version used.

2. **`genai.GenerativeModel()` for Async**: We explored using
   `model = genai.GenerativeModel(effective_model_name)` followed by
   `await model.generate_content_async(...)`. While this pattern is valid for
   some use cases (especially simpler, direct API key usage without the full
   client setup), the `client.aio.models` approach is more aligned with the
   example provided for robust client-based interaction, especially when
   `HttpOptions` might be relevant.

3. **Incorrect `genai.Client()` Method Calls**: Several `AttributeError` and
   `TypeError` exceptions were encountered due to incorrect assumptions about
   the `genai.Client` object's methods for asynchronous calls:
   - `client.models.generate_content_async(...)`: This method does not exist
     directly on `client.models`. The `models` attribute is a manager, and async
     methods are typically under an `aio` namespace or on the model instance
     itself.
   - `client.models.get(...).generate_content_async(...)`: While
     `client.models.get()` retrieves a model _description/handler_, the
     subsequent call to `generate_content_async` on this object was not the
     correct pattern for the `google.genai` client's async operations.

4. **Clarity from Documentation/Examples**: The provided example
   (`genai async generation.md`) using `client.aio.models.generate_content` with
   `HttpOptions` was key to identifying the current correct pattern for
   asynchronous, client-based interaction with Vertex AI.

5. **Incorrect `genai.Client` Initialization for Vertex AI**: A critical `TypeError` was encountered when attempting to configure the client for a specific Vertex AI endpoint, such as the `global` location required for `gemini-embedding-001`.
   - **Symptom**: `TypeError: Client.__init__() got an unexpected keyword argument 'client_options'`.
   - **Cause**: This error was the result of incorrectly attempting to pass a dictionary of `client_options={"api_endpoint": "..."}` to the `genai.Client` constructor. This parameter is not supported by the SDK for this purpose.
   - **Resolution**: The official `google-genai` SDK documentation confirms that the correct method for initializing a client for Vertex AI is to pass specific keyword arguments directly to the constructor. This provides a clean, explicit, and validated way to configure the client.

     ```python
     # CORRECT way to initialize the client for Vertex AI
     # The project and location should be sourced from a central configuration.

     client = genai.Client(
         vertexai=True,
         project='your-gcp-project-id',
         location='your-gcp-location' # e.g., 'us-central1' or 'global' for embeddings
     )
     ```
   - **Key Takeaway**: Do not invent parameters like `client_options` or attempt to manually construct endpoint URLs. Always use the documented keyword arguments (`vertexai`, `project`, `location`) for Vertex AI client configuration. For standard Google AI Studio access (non-Vertex), the client is simply initialized with `genai.Client()`, which will then use Application Default Credentials (ADC) or the `GOOGLE_API_KEY` environment variable.

6. **Correct Source for Vertex AI Project ID**: When using the `google-genai` SDK with Vertex AI and Application Default Credentials (ADC), the GCP Project ID should be sourced directly from the environment.
   - **Symptom**: `AttributeError: 'IngestionOrchestratorConfig' object has no attribute 'google'`.
   - **Cause**: This error occurred because the code attempted to access the project ID from a Pydantic configuration object (`config.google.gcp_project_id`), but the ID is not defined there.
   - **Resolution**: The correct approach is to retrieve the project ID from the `GOOGLE_CLOUD_PROJECT` environment variable (`os.environ.get("GOOGLE_CLOUD_PROJECT")`). The SDK is designed to look for this variable automatically when ADC is used.
   - **Key Takeaway**: For services using ADC, rely on the standard environment variables (`GOOGLE_CLOUD_PROJECT`, `GOOGLE_CLOUD_LOCATION`) that the underlying Google Cloud libraries expect. Avoid duplicating this configuration in application-level config files unless there is a specific reason to override it.

This document should be updated if new SDK versions introduce changes or if
further best practices are discovered.
