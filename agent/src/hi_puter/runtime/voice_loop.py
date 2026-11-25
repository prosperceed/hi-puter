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
from collections.abc import Callable
from threading import Event

from hi_puter.audio.listener import UtteranceSource
from hi_puter.brain.assistant import Assistant, Reply, is_yes
from hi_puter.core.config import VoiceConfig
from hi_puter.speech.stt import Transcriber
from hi_puter.speech.tts import Synthesizer
from hi_puter.speech.wake import match_wake

log = logging.getLogger("hi_puter")


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

    def run(self) -> None:
        log.info("Listening for %r", self.wake_name)
        while not self.stop.is_set():
            self.step()

    def step(self) -> None:
        """Wait for one utterance; start a session if it begins with the wake name."""
        heard = self._hear(None)
        if heard is None:
            return
        wake = match_wake(heard, self.wake_name, self.wake_threshold)
        if wake is None:
            return
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
            self.assistant.reset()
            log.info("Session ended; listening for %r", self.wake_name)

    def _respond(self, request: str) -> Reply:
        if not self.assistant.is_quick(request) and self.voice.working_phrase:
            self._say(self.voice.working_phrase)
        reply = self.assistant.handle(request)
        self._say(reply.text)
        if reply.pending is None:
            return reply
        answer = self._hear(self.voice.prompt_timeout_seconds)
        result = self.assistant.confirm(reply.pending, is_yes(answer))
        self._say(result.text)
        return result

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
        text = self.stt.transcribe(audio).strip()
        if self.log_transcripts and text:
            log.info("Heard: %s", text)
        return text or None
