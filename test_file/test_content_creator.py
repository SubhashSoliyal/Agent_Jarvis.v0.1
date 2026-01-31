import asyncio
import os
from backend.Jarvis_content_creator import generate_content_nvidia, read_content_for_feedback, refine_content_nvidia

async def main():
    print("--- Testing Content Creator ---")
    
    # 1. Generate
    print("\n1. Generating Content...")
    topic = "The friendly robot Jarvis"
    content_type = "Short Story"
    result = await generate_content_nvidia(topic, content_type, "Make it under 50 words.")
    print(result)
    
    if "❌" in result:
        print("Stopping due to error.")
        return

    # Extract filename from result (simplified logic for test)
    # The result string has "saved to: filename"
    # let's just guess the filename based on logic
    filename = f"{topic.replace(' ', '_')}_{content_type.replace(' ', '_')}.txt"
    # Wait, my code does: topic.replace(" ", "_")...[:30] + ...
    # Let's inspect the folder to find it or parse the output if I could, but for this test I'll just look for the file.
    
    print("\n2. Reading Content...")
    # I need the exact filename. My tool returns it.
    # Let's list the dir to find it.
    content_dir = os.path.join("backend", "Data", "Content")
    files = os.listdir(content_dir)
    print(f"Files in content dir: {files}")
    
    # Pick the latest one or the one matching our topic
    target_file = None
    for f in files:
        if "friendly_robot_Jarvis" in f: # approximate match
             target_file = f
             break
    
    if target_file:
        print(f"Targeting file: {target_file}")
        read_result = await read_content_for_feedback(target_file)
        print(read_result)
        
        print("\n3. Refining Content...")
        refine_result = await refine_content_nvidia(target_file, "Add a cat to the story.")
        print(refine_result)
        
        print("\n4. verifying refinement...")
        read_result_2 = await read_content_for_feedback(target_file)
        print(read_result_2)
        
    else:
        print("Could not find generated file to test read/refine.")

if __name__ == "__main__":
    asyncio.run(main())
