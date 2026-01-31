
from test_file.nvidia import call_llm

print("Testing call_llm with 'Hello'...")
try:
    response = call_llm("Hello")
    print("Response received:")
    print(response)
except Exception as e:
    print(f"Error: {e}")
