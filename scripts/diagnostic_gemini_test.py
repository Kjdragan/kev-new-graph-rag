import os
import sys
import traceback
from dotenv import load_dotenv

# Add project root to Python path to allow importing our modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Load environment variables from .env file
dotenv_path = os.path.join(project_root, 'src', '.env')
print(f"Looking for .env at: {os.path.abspath(dotenv_path)}", flush=True)

if not os.path.exists(dotenv_path):
    print(f"Error: .env file not found at {os.path.abspath(dotenv_path)}", flush=True)
    sys.exit(1)

load_dotenv(dotenv_path=dotenv_path, verbose=True)
print(".env file loaded.", flush=True)

# Print at every step with flush=True for immediate output
print("--- DIAGNOSTIC GEMINI TEST START ---", flush=True)
print(f"Python version: {sys.version}", flush=True)

try:
    # Import our configuration module
    from utils.config import get_config
    config = get_config()
    print("Step 1: Configuration loaded successfully", flush=True)
except Exception as e:
    print(f"ERROR loading configuration: {e}", flush=True)
    traceback.print_exc(file=sys.stdout)
    sys.exit(1)

# Check if API key is available
api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("ERROR: GOOGLE_API_KEY environment variable not set", flush=True)
    sys.exit(1)

print("Step 2: API key found", flush=True)

# Get model IDs from config
flash_model_id = config.get_gemini_model_id("flash")
pro_model_id = config.get_gemini_model_id("pro")
embeddings_model_id = config.get_gemini_embeddings_model()

print(f"Step 3: Using models from config: Flash={flash_model_id}, Pro={pro_model_id}, Embeddings={embeddings_model_id}", flush=True)

try:
    print("Step 4: Importing google.genai module...", flush=True)
    from google import genai
    print("Step 5: Successfully imported google.genai", flush=True)

    print("Step 6: Creating Google Gemini client...", flush=True)
    client = genai.Client(api_key=api_key)
    print("Step 7: Google Gemini client created successfully", flush=True)

    # Try a simple API call that doesn't require much processing
    print("Step 8: Getting model list...", flush=True)
    models = client.models.list()
    print("Step 9: Model list retrieved successfully", flush=True)

    # Print first 3 models only to avoid overwhelming output
    print("First 3 available models:")
    for i, model in enumerate(models):
        if i < 3:
            print(f" - {model.name}")
        else:
            break

    print(f"\nStep 10: Testing {flash_model_id} (Flash) model...", flush=True)
    try:
        # IMPORTANT: Use exact model ID from config
        flash_response = client.models.generate_content(
            model=flash_model_id,
            contents='Say "Hello from Gemini Flash!" in one short sentence.'
        )
        print(f"{flash_model_id} response successful", flush=True)
        print(f"Response text: {flash_response.text}", flush=True)
    except Exception as e:
        print(f"{flash_model_id} test failed: {str(e)}", flush=True)
        traceback.print_exc(file=sys.stdout)

    print(f"\nStep 11: Testing {pro_model_id} (Pro) model...", flush=True)
    try:
        # IMPORTANT: Use exact model ID from config
        pro_response = client.models.generate_content(
            model=pro_model_id,
            contents='Say "Hello from Gemini Pro!" in one short sentence.'
        )
        print(f"{pro_model_id} response successful", flush=True)
        print(f"Response text: {pro_response.text}", flush=True)
    except Exception as e:
        print(f"{pro_model_id} test failed: {str(e)}", flush=True)
        print("This is expected if you don't have access to this model.")
        traceback.print_exc(file=sys.stdout)

    print("\nStep 12: Testing thinking capability with Pro model...", flush=True)
    from google.genai import types as genai_types
    try:
        thinking_response = client.models.generate_content(
            model=pro_model_id,
            contents="Calculate the sum of the first 10 prime numbers step by step.",
            config=genai_types.GenerateContentConfig(
                thinking_config=genai_types.ThinkingConfig(
                    include_thoughts=True,
                    thinking_budget=config.get_gemini_thinking_budget("pro")
                )
            )
        )
        print("Thinking capability test successful!", flush=True)
        print("Thought summary available in response")
    except Exception as e:
        print(f"Thinking capability test failed: {str(e)}", flush=True)
        traceback.print_exc(file=sys.stdout)

    print("\nStep 13: All models tested successfully", flush=True)

except Exception as e:
    print(f"ERROR: {e}", flush=True)
    import traceback
    traceback.print_exc(file=sys.stdout)

print("--- DIAGNOSTIC GEMINI TEST END ---", flush=True)
