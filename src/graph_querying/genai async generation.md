Generative AI on Vertex AI Documentation Vertex AI Cookbook Was this helpful?

Async example to Generate content with Multimodal AI Model

bookmark_border The code sample demonstrates how to use Generative AI Models
using async feature

Code sample Python Before trying this sample, follow the Python setup
instructions in the Vertex AI quickstart using client libraries. For more
information, see the Vertex AI Python API reference documentation.

To authenticate to Vertex AI, set up Application Default Credentials. For more
information, see Set up authentication for a local development environment.

from google import genai from google.genai.types import GenerateContentConfig,
HttpOptions

client = genai.Client(http_options=HttpOptions(api_version="v1")) model_id =
"gemini-2.5-flash"

response = await client.aio.models.generate_content( model=model_id,
contents="Compose a song about the adventures of a time-traveling squirrel.",
config=GenerateContentConfig( response_modalities=["TEXT"], ), )

print(response.text)

# Example response:

# (Verse 1)

# Sammy the squirrel, a furry little friend

# Had a knack for adventure, beyond all comprehend
