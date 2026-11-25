"""The spoken conversation.

    passive ── hears "Nova" ──▶ chime + "Listening." ──▶ waits for the request
       ▲                                                   │
       │                                   "On it." (model requests) + execute
       │                                                   │
       └── silence ◀── follow-up window (no wake name) ◀── speaks the result
                                                           │
                               risky action: asks, waits for "yes", then runs

"Nova, open Firefox" in one breath skips the "Listening." step.
"""

import logging
import re
from collections.abc import Callable
from threading import Event
from time import monotonic

from hi_puter.audio.listener import UtteranceSource
from hi_puter.brain.assistant import Assistant, Reply, is_yes
from hi_puter.core.config import VoiceConfig
from hi_puter.nlu.normalize import normalize
from hi_puter.speech.stt import Transcriber
from hi_puter.speech.tts import Synthesizer
from hi_puter.speech.wake import match_wake

log = logging.getLogger("hi_puter")

# 2.5 s of 16 kHz 16-bit mono: long enough for "Hey <two-word name>" plus a pause.
WAKE_WINDOW_BYTES = int(2.5 * 16_000 * 2)


# Said on their own, these end a dictation.
FINISHED_ALONE = frozenset(
    {"done", "i'm done", "im done", "i am done", "that's it", "thats it", "that's all",
     "thats all", "finished", "i'm finished", "the end", "end", "end dictation", "stop"}
)  # fmt: skip
# Said at the end of a longer utterance, these also end it ("...and that's all").
FINISHED_TAIL = re.compile(
    r"[\s,.;:!-]*\b(?:i'?m done|i am done|that'?s all|end of (?:the )?dictation|end dictation)"
    r"[\s.!]*$",
    re.IGNORECASE,
)


def split_finished(heard: str) -> tuple[bool, str]:
    """(whether the user finished dictating, the words to keep)."""
    if normalize(heard) in FINISHED_ALONE:
        return True, ""
    kept, count = FINISHED_TAIL.subn("", heard)
    return (True, kept.strip()) if count else (False, heard.strip())


class VoiceLoop:
    def __init__(
        self,
        *,
        source: UtteranceSource,
        stt: Transcriber,
        tts: Synthesizer,
        assistant: Assistant,
        wake_name: str,
        wake_threshold: float,
        voice: VoiceConfig,
        stop: Event,
        chime: Callable[[], None] | None = None,
        log_transcripts: bool = False,
        dictation_pause_seconds: float = 10.0,
        dictation_max_seconds: float = 600.0,
    ) -> None:
        self.source = source
        self.stt = stt
        self.tts = tts
        self.assistant = assistant
        self.wake_name = wake_name
        self.wake_threshold = wake_threshold
        self.voice = voice
        self.stop = stop
        self.chime = chime
        self.log_transcripts = log_transcripts
        self.dictation_pause_seconds = dictation_pause_seconds
        self.dictation_max_seconds = dictation_max_seconds

    def run(self) -> None:
        log.info("Listening for %r", self.wake_name)
        while not self.stop.is_set():
            self.step()

    def step(self) -> None:
        """Wait for one utterance; start a session if it begins with the wake name."""
        audio = self.source.next_utterance(None)
        if audio is None:
            return
        # The name comes first, so only the start of background talk is worth transcribing.
        wake = match_wake(
            self._transcribe(audio[:WAKE_WINDOW_BYTES]), self.wake_name, self.wake_threshold
        )
        if wake is None:
            return
        if len(audio) > WAKE_WINDOW_BYTES:
            full = match_wake(self._transcribe(audio), self.wake_name, self.wake_threshold)
            wake = full or wake
        log.info("Wake name heard (score %.2f)", wake.score)
        self.session(wake.remainder)

    def session(self, first_request: str = "") -> None:
        request: str | None = first_request.strip()
        if not request:
            self._acknowledge()
            request = self._hear(self.voice.prompt_timeout_seconds)
            if not request:
                log.info("No request after the wake name")
                return
        try:
            while request and not self.stop.is_set():
                reply = self._respond(request)
                if reply.end_session or self.voice.followup_seconds <= 0:
                    break
                request = self._hear(self.voice.followup_seconds)
                if request:
                    # "Nova, and mute it" during the follow-up window: drop the name.
                    wake = match_wake(request, self.wake_name, self.wake_threshold)
                    if wake is not None:
                        request = wake.remainder or None
                        if request is None:
                            self._acknowledge()
                            request = self._hear(self.voice.prompt_timeout_seconds)
        finally:
            # The conversation is kept: the model's cache can only be extended, and starting
            # over makes the next request re-read the whole prompt.
            log.info("Session ended; listening for %r", self.wake_name)

    def _respond(self, request: str) -> Reply:
        if not self.assistant.is_quick(request) and self.voice.working_phrase:
            self._say(self.voice.working_phrase)
        reply = self.assistant.handle(request)
        self._say(reply.text)
        if reply.dictation is not None:
            words = self._dictate()
            if words:
                self._say(
                    f"Got it. Writing your {reply.dictation.kind} now; this can take a minute."
                )
            result = self.assistant.write_document(words, reply.dictation)
            self._say(result.text)
            return result
        if reply.pending is None:
            return reply
        answer = self._hear(self.voice.prompt_timeout_seconds)
        result = self.assistant.confirm(reply.pending, is_yes(answer))
        self._say(result.text)
        return result

    def _dictate(self) -> str:
        """Collect what the user says, across pauses, until they say "done" or go quiet."""
        parts: list[str] = []
        started = monotonic()
        while not self.stop.is_set() and monotonic() - started < self.dictation_max_seconds:
            # Allow a moment to start; after that, a long pause means they've finished.
            wait = self.dictation_pause_seconds if parts else 2 * self.voice.prompt_timeout_seconds
            heard = self._hear(wait)
            if heard is None:
                break
            finished, kept = split_finished(heard)
            if kept:
                parts.append(kept)
            if finished:
                break
        log.info("Dictation: %d words", sum(len(part.split()) for part in parts))
        return " ".join(parts)

    def _acknowledge(self) -> None:
        if self.voice.chime and self.chime is not None:
            self.chime()
        if self.voice.listening_phrase:
            self._say(self.voice.listening_phrase)
        else:
            self.source.flush()

    def _say(self, text: str) -> None:
        if text:
            log.info("Say: %s", text)
            self.tts.speak(text)
        # Don't transcribe our own voice.
        self.source.flush()

    def _hear(self, start_timeout: float | None) -> str | None:
        audio = self.source.next_utterance(start_timeout)
        if audio is None:
            return None
        return self._transcribe(audio) or None

    def _transcribe(self, audio: bytes) -> str:
        text = self.stt.transcribe(audio).strip()
        if self.log_transcripts and text:
            log.info("Heard: %s", text)
        return text
