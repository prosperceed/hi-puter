class WakeDetector:
    def __init__(self, wake_name: str, threshold: float = 0.65) -> None:
        self.wake_name = wake_name.lower(); self.threshold = threshold
    def matches(self, text: str, confidence: float) -> bool:
        return confidence >= self.threshold and text.lower().strip().startswith(self.wake_name)
