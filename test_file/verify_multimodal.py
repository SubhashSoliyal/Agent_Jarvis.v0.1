try:
    from livekit.agents.multimodal import MultimodalAgent
    print("MultimodalAgent imported successfully")
except ImportError as e:
    print(f"Import failed: {e}")

try:
    from livekit.plugins.google.beta.realtime import RealtimeModel
    print("RealtimeModel imported successfully")
except ImportError as e:
    print(f"RealtimeModel failed: {e}")
