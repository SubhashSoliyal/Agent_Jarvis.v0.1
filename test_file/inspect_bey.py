import inspect
from livekit.plugins import bey

with open("bey_info.txt", "w") as f:
    f.write("Contents of livekit.plugins.bey:\n")
    for name, obj in inspect.getmembers(bey):
        if not name.startswith("__"):
            f.write(f"{name}: {obj}\n")
            if inspect.isclass(obj) or inspect.isfunction(obj):
                 f.write(f"  Doc: {obj.__doc__}\n")
                 try:
                    f.write(f"  Sig: {inspect.signature(obj)}\n")
                 except:
                    pass
