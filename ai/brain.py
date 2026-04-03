import aiohttp
import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY, OLLAMA_URL, PREFERRED_MODEL
from ai.prompt_engine import build_event_prompt
from ai.action_parser import parse_ai_response

async def detect_local_model():
    """
    Detects if a local model is running (Ollama default: localhost:11434)
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_URL}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model["name"] for model in data.get("models", [])]
    except Exception:
        return []

async def ask_ai(event_context):
    """
    AI model router (cloud / local)
    """
    prompt = build_event_prompt(event_context)

    # Try local Ollama first if preferred or auto
    if PREFERRED_MODEL in ["auto", "ollama"]:
        local_models = await detect_local_model()
        if local_models:
            # Use the first available model, or a specific one if specified
            model_name = local_models[0] # Simplification
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(f"{OLLAMA_URL}/api/generate", json={
                        "model": model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }) as response:
                        if response.status == 200:
                            data = await response.json()
                            return parse_ai_response(data.get("response"))
            except Exception as e:
                print(f"Error calling local AI: {e}")

    # Fallback to Gemini
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model_name = PREFERRED_MODEL if PREFERRED_MODEL != "auto" else "gemini-1.5-flash"
            model = genai.GenerativeModel(model_name)
            response = await model.generate_content_async(prompt)
            return parse_ai_response(response.text)
        except Exception as e:
            print(f"Error calling Gemini: {e}")

    return None
