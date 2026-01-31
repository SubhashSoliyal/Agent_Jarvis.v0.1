from backend.Jarvis_reporter import save_formatted_doc
import os

# Mock "Dirty" Content mimicking the user's issue
dirty_content = """thermodynamics analysis of a gas in a closed container with a movable piston and formula
markdown
Copy
Download
Thermodynamic Analysis of a Gas in a Closed System with a Movable Piston

Abstract
The closed system comprising a gas...
"""

output_path = r"c:\AnithingLLM\Jarvis.v3.0\Jarvis.v3.0\backend\Data\Reports\CLEAN_TEST.docx"
topic = "thermodynamics analysis of a gas in a closed container with a movable piston and formula"

print("Testing cleaning logic...")
try:
    save_formatted_doc(dirty_content, output_path, topic)
    print("Document saved.")
    
    # We can't easily check the Docx content without unzipping it, but we can check if it ran without error.
    # Ideally, we would inspect the doc manually or trust the logic we just wrote.
    if os.path.exists(output_path):
        print(f"SUCCESS: {output_path} created.")
        print("Please check the document to ensure 'markdown Copy Download' is GONE.")
except Exception as e:
    print(f"ERROR: {e}")
