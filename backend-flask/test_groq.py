"""Quick smoke test for Groq connectivity."""
import os
from dotenv import load_dotenv
load_dotenv()

from services.llm import send_message

if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "").startswith("your_"):
        print("Set GROQ_API_KEY in backend-flask/.env first.")
        raise SystemExit(1)
    print(send_message("Say hi in one short sentence as NutriBot."))
