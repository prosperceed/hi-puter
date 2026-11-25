import logging

log = logging.getLogger("hi_puter")


def play_listening_cue(volume: float = 0.18) -> None:
    """A short rising two-note chime. Silent if sounddevice or numpy is missing."""
    try:
        import numpy as np
        import sounddevice
    except ImportError:
        return
    rate = 22_050
    notes = []
    for frequency in (880.0, 1320.0):
        t = np.linspace(0, 0.075, int(rate * 0.075), endpoint=False)
        envelope = np.minimum(1.0, np.minimum(t / 0.008, (0.075 - t) / 0.03))
        notes.append(np.sin(2 * np.pi * frequency * t) * envelope)
    wave = (np.concatenate(notes) * volume).astype(np.float32)
    try:
        sounddevice.play(wave, rate)
        sounddevice.wait()
    except Exception as exc:  # no output device
        log.info("Could not play chime: %s", exc)
