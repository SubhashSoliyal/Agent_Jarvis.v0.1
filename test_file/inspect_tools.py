
import sys
import os
import asyncio
from backend.Jarvis_reporter import generate_deepseek_report, generate_deepseek_research_paper

print(f"Type of generate_deepseek_report: {type(generate_deepseek_report)}")
print(f"Dir: {dir(generate_deepseek_report)}")

# If it is a FunctionTool, it might have a 'callable' attribute or we might need to access the underlying function
try:
    if hasattr(generate_deepseek_report, 'callable'):
        print("Has callable attribute")
    if hasattr(generate_deepseek_report, 'fn'):
        print("Has fn attribute")
except:
    pass
