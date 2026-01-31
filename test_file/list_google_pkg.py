import livekit.plugins.google
import os

path = os.path.dirname(livekit.plugins.google.__file__)
print(f"Path: {path}")
print("Contents:")
def list_recursive(d, indent=0):
    for f in os.listdir(d):
        if f == "__pycache__": continue
        print("  " * indent + f)
        full_path = os.path.join(d, f)
        if os.path.isdir(full_path):
            list_recursive(full_path, indent + 1)

list_recursive(path)
