
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("BEY_API_KEY")
aid = os.getenv("BEY_AVATAR_ID")

print(f"BEY_API_KEY loaded: '{key}'")
print(f"BEY_AVATAR_ID loaded: '{aid}'")

if key and key.startswith('"') and key.endswith('"'):
    print("WARNING: Keys contain quotes!")
else:
    print("Keys format looks OK (no surrounding quotes).")
