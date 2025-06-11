import os
import asyncio
from dotenv import load_dotenv
from google import genai

async def test_minimal_gemini():
    """Test minimal Gemini API initialization"""
    print("--- test_minimal_gemini started ---", flush=True)
    
    # Load environment variables 
    dotenv_path = os.path.join(os.path.dirname(__file__), '..', 'src', '.env')
    if not os.path.exists(dotenv_path):
        print(f"Error: .env file not found at {os.path.abspath(dotenv_path)}", flush=True)
        return
    load_dotenv(dotenv_path=dotenv_path, verbose=True)
    print(".env file loaded.", flush=True)
    
    # Get API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: Google API key not set.", flush=True)
        return
    
    print("Google API Key found: [REDACTED]", flush=True)
    
    # Create Gemini API client
    try:
        print("Creating Google Gemini client...", flush=True)
        client = genai.Client(api_key=google_api_key)
        print("Google Gemini client created successfully.", flush=True)
        
        # List models to verify API works
        print("Listing available Gemini models...", flush=True)
        models = client.models.list()
        print("Models available:")
        for model in models:
            print(f" - {model.name}")
        
        print("Gemini API test completed successfully.", flush=True)
        
    except Exception as e:
        print(f"Error with Gemini API: {e}", flush=True)
        import traceback
        traceback.print_exc()

async def main():
    print("--- Script execution started ---", flush=True)
    await test_minimal_gemini()
    print("--- Script execution finished ---", flush=True)

if __name__ == "__main__":
    print("--- MINIMAL GEMINI TEST STARTING ---", flush=True)
    print("--- BEFORE ASYNCIO.RUN(MAIN) ---", flush=True)
    asyncio.run(main())
    print("--- AFTER ASYNCIO.RUN(MAIN) ---", flush=True)
