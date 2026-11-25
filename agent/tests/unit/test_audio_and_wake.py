from hi_puter.audio.segmenter import UtteranceSegmenter
from hi_puter.speech.stt import is_noise
from hi_puter.speech.wake import match_wake

SPEECH, QUIET = True, False


def feed(segmenter: UtteranceSegmenter, pattern: list[bool]) -> list[bytes]:
    done = []
    for index, voiced in enumerate(pattern):
        result = segmenter.push(bytes([index % 256]) * 960, voiced)
        if result is not None:
            done.append(result)
    return done


def test_utterance_ends_after_silence_and_keeps_preroll() -> None:
    segmenter = UtteranceSegmenter(end_silence_ms=300, preroll_ms=150)
    pattern = [QUIET] * 10 + [SPEECH] * 20 + [QUIET] * 10
    (utterance,) = feed(segmenter, pattern)
    frames = len(utterance) // 960
    assert 20 <= frames <= 20 + 5 + 10  # speech + pre-roll + trailing silence
    assert not segmenter.in_speech


def test_short_bursts_are_dropped() -> None:
    segmenter = UtteranceSegmenter(end_silence_ms=300, min_speech_ms=240)
    assert feed(segmenter, [QUIET] * 5 + [SPEECH] * 3 + [QUIET] * 15) == []


def test_long_speech_is_cut_at_max_length() -> None:
    segmenter = UtteranceSegmenter(max_seconds=0.6)
    assert len(feed(segmenter, [SPEECH] * 50)) >= 2


def test_wake_match_variants() -> None:
    assert match_wake("Nova, open Firefox.", "nova") is not None
    assert match_wake("Nova, open Firefox.", "nova").remainder == "open firefox"  # type: ignore[union-attr]
    assert match_wake("hey nova what time is it", "nova").remainder == "what time is it"  # type: ignore[union-attr]
    assert match_wake("Novah", "nova") is not None  # small mis-hearing
    assert (
        match_wake("my assistant, lock the screen", "my assistant").remainder == "lock the screen"
    )  # type: ignore[union-attr]


def test_wake_name_must_be_at_the_start() -> None:
    assert match_wake("I like the name nova", "nova") is None
    assert match_wake("no way", "nova") is None
    assert match_wake("", "nova") is None


def test_whisper_noise_filter() -> None:
    assert is_noise("Thank you.") and is_noise(" you ")
    assert not is_noise("Nova, thank you for the help")
