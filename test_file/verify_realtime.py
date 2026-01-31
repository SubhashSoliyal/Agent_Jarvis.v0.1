try:
    from livekit.plugins.google.realtime import RealtimeModel
    print("RealtimeModel imported successfully from livekit.plugins.google.realtime")
except ImportError as e:
    print(f"RealtimeModel failed: {e}")
