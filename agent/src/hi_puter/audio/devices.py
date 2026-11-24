def list_input_devices() -> list[str]:
    import sounddevice
    return [str(device["name"]) for device in sounddevice.query_devices() if device["max_input_channels"] > 0]
