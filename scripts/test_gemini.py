# scripts/test_gemini.py
import sys
from pathlib import Path

# Add backend to sys.path so we can import app modules
backend_dir = Path(__file__).resolve().parents[1] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

def test_model(model_name: str):
    api_key_str = settings.GOOGLE_API_KEY.get_secret_value() if settings.GOOGLE_API_KEY else ""
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=api_key_str,
            temperature=0.1,
        )
        res = llm.invoke([HumanMessage(content="Hello, what is 2+2?")])
        content = res.content
        if isinstance(content, list):
            text = " ".join(item.get("text", "") for item in content if isinstance(item, dict))
        else:
            text = str(content)
        cleaned = text.replace("\n", " ")[:100]
        print(f"Model: {model_name} | Success: True | Error: None | Response: {cleaned}")
        return True
    except Exception as e:
        err_msg = str(e)
        if api_key_str and api_key_str in err_msg:
            err_msg = err_msg.replace(api_key_str, "[REDACTED_API_KEY]")
        print(f"Model: {model_name} | Success: False | Error: {type(e).__name__}: {err_msg[:120]} | Response: None")
        return False

if __name__ == "__main__":
    configured_model = settings.GEMINI_MODEL
    print(f"Testing configured GEMINI_MODEL: {configured_model}")
    success = test_model(configured_model)
    if not success:
        for candidate in ["gemini-3.8-flash", "gemini-flash-latest", "gemini-2.5-flash"]:
            if candidate != configured_model:
                print(f"Testing fallback candidate: {candidate}")
                if test_model(candidate):
                    break

