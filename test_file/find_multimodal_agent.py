import livekit.agents
import pkgutil
import importlib
import sys

def find_class(package, target):
    path = getattr(package, "__path__", [])
    if not path:
        return
        
    for _, name, is_pkg in pkgutil.walk_packages(path, package.__name__ + "."):
        try:
            mod = importlib.import_module(name)
            if hasattr(mod, target):
                print(f"Found {target} in {name}")
                return
        except Exception:
            pass

print("Searching for MultimodalAgent...")
find_class(livekit.agents, "MultimodalAgent")
print("Search done.")
