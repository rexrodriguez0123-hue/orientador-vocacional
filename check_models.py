import google.generativeai as genai
import os

api_key = os.environ.get("GOOGLE_API_KEY")

if not api_key:
    print("No API Key found. Skipping list_models check.")
else:
    genai.configure(api_key=api_key)
    try:
        print("Available models:")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
    except Exception as e:
        print(f"Error listing models: {e}")
