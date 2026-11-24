class VoiceActivityDetector:
    def __init__(self, aggressiveness: int = 2) -> None:
        import webrtcvad
        self._vad = webrtcvad.Vad(aggressiveness)
    def is_speech(self, frame: bytes, sample_rate: int = 16_000) -> bool: return self._vad.is_speech(frame, sample_rate)
