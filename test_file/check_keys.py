import os
from dotenv import load_dotenv

load_dotenv()

keys = ["GOOGLE_API_KEY", "OPENAI_API_KEY", "DEEPGRAM_API_KEY", "AZURE_SPEECH_KEY"]
print("Available Keys:")
for k in keys:
    val = os.getenv(k)
    if val:
        print(f"{k}: Present")
    else:
        print(f"{k}: Missing")
