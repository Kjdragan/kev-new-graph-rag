# Google Generative AI SDK Migration Notes

## Current Correct SDK

The correct Google SDK to use for Gemini models is `google-genai`.

## SDK Migration Information

### Installation
```bash
# OLD (deprecated)
pip install -U google-generativeai

# NEW (correct)
pip install -U google-genai
```

For our project, use:
```bash
uv add google-genai
```

### Key Differences

1. **Import Statements**:
   - OLD: `import google.generativeai as genai`
   - NEW: `from google import genai`

2. **Client Initialization**:
   - OLD: `genai.configure(api_key=...)`
   - NEW: `client = genai.Client(api_key=...)`

3. **Model Usage**:
   - OLD: 
     ```python
     model = genai.GenerativeModel('gemini-1.5-flash')
     response = model.generate_content('prompt')
     ```
   - NEW:
     ```python
     response = client.models.generate_content(
         model='gemini-2.0-flash',
         contents='prompt'
     )
     ```

4. **Embedding Generation**:
   - OLD:
     ```python
     result = genai.embed_content(model="embedding-001", content=text)
     ```
   - NEW:
     ```python
     # Initialize the client (typically done once)
     client = genai.Client(api_key="YOUR_API_KEY")

     # Call client.models.embed_content
     result = client.models.embed_content(
         model="gemini-embedding-exp-03-07", # Or your specific embedding model ID
         contents=[text], # API expects a list of contents
         task_type="RETRIEVAL_DOCUMENT" # Or other relevant task types e.g., "SEMANTIC_SIMILARITY"
     )
     # result.embeddings is a list of Embedding objects.
     # For a single input text, access the first embedding's values:
     embedding_vector = result.embeddings[0].values
     ```

### Response Structure
The new SDK uses pydantic classes for responses, providing better type safety and consistent structure.

### Configuration
Configuration is now more structured and passed through the `config` parameter:
```python
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.0-flash',
    contents='prompt',
    config=types.GenerateContentConfig(
        temperature=0.5,
        top_k=40,
        top_p=0.95,
        max_output_tokens=1000,
    )
)
```

## Implementation Note
For the embedding implementation in our project, we should update the `CustomGeminiEmbedding` class to use the new SDK pattern.
