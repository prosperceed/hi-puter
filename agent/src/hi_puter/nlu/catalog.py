from dataclasses import dataclass
from enum import Enum


class Risk(str, Enum):
    SAFE = "safe"
    CONFIRM = "confirm"


@dataclass(frozen=True)
class Intent:
    id: str
    action: str
    slots: dict[str, str]
    risk: Risk = Risk.SAFE


# Spoken site names that open in the browser instead of looking for an app.
SITES = {
    "youtube": "youtube.com",
    "gmail": "mail.google.com",
    "google": "google.com",
    "google maps": "maps.google.com",
    "maps": "maps.google.com",
    "github": "github.com",
    "netflix": "netflix.com",
    "reddit": "reddit.com",
    "wikipedia": "wikipedia.org",
    "twitter": "x.com",
    "facebook": "facebook.com",
    "instagram": "instagram.com",
    "linkedin": "linkedin.com",
    "whatsapp web": "web.whatsapp.com",
    "chatgpt": "chatgpt.com",
}
_SITE_NAMES = "|".join(sorted(SITES, key=len, reverse=True))
_DOCUMENTS = (
    r"(?:document|doc|letter|cover letter|email|e-mail|essay|report|article|blog post|memo"
    r"|proposal|story|speech|summary)"
)
# Players named without "on": "pause spotify", "next song spotify".
_PLAYERS = r"(?:spotify|vlc|rhythmbox|youtube music|youtube|firefox|chrome|chromium|music)"
_DEVICE = r"(?: (?:the|my))?(?: computer| pc| laptop)?"

# Order matters: the first pattern that matches wins.
PATTERNS: tuple[tuple[str, str, str, Risk], ...] = (
    ("shutdown", rf"^(?:shut down|shutdown|turn off|power off){_DEVICE}$", "power", Risk.CONFIRM),
    ("restart", rf"^(?:restart|reboot){_DEVICE}$", "power", Risk.CONFIRM),
    (
        "suspend",
        r"^(?:suspend|sleep|put (?:the |my )?(?:computer|pc|laptop) to sleep)$",
        "power",
        Risk.CONFIRM,
    ),
    (
        "open_site",
        rf"^(?:open|launch|go to|show me) (?P<site>{_SITE_NAMES})$",
        "open_site",
        Risk.SAFE,
    ),
    (
        "open_site",
        r"^(?:open|go to) (?P<site>[a-z0-9-]+(?:\.[a-z0-9-]+)+(?:/\S*)?)$",
        "open_site",
        Risk.SAFE,
    ),
    (
        "start_document",
        r"^(?:(?:help me |i want to |i'?d like to |let'?s |can we |can you )?"
        r"(?:write|draft|compose|create|start|make|prepare)(?: me)?(?: up)?"
        r" (?:a |an |the |my |a new |new )?"
        rf"(?P<kind>{_DOCUMENTS})"
        r"(?: (?P<topic>(?:about|on|for|to|regarding|thanking|asking|telling) .+))?)$",
        "start_document",
        Risk.SAFE,
    ),
    (
        "open_document",
        rf"^(?:open|show me|show)(?: up)? (?:the |my |that )(?:{_DOCUMENTS})(?: again)?$",
        "open_document",
        Risk.SAFE,
    ),
    (
        "stop_recording",
        r"^(?:stop|end|finish|save)(?: the| my)?(?: screen)? (?:recording|recorder|screencast)"
        r"(?: (?:the|my) screen)?$",
        "stop_recording",
        Risk.SAFE,
    ),
    (
        "start_recording",
        r"^(?:(?:start|begin)(?: a| the)?(?: screen)? (?:recording|screencast)(?: the screen)?"
        r"|record(?: the| my)? screen|(?:open|bring up|start|launch|show)(?: the| a)?"
        r" screen ?recorder)"
        r"(?: for (?P<amount>\d+|a|an|one|two|three|four|five|ten|fifteen|twenty|thirty)"
        r" (?P<unit>seconds?|minutes?))?$",
        "start_recording",
        Risk.SAFE,
    ),
    (
        "screenshot_choose",
        r"^(?:(?:take |grab )?(?:a )?screen ?shot (?:of )?(?:a |an |the |this |one )?"
        r"(?:window|area|part|region|selection|section)(?: of the screen)?"
        r"|(?:open|bring up|show)(?: the)? screen ?shot(?: tool| app| menu)?)$",
        "screenshot_choose",
        Risk.SAFE,
    ),
    (
        "close_app",
        r"^(?:close|quit|exit|kill|shut|turn off)(?: down)? "
        r"(?!(?:the |my )?(?:computer|pc|laptop|screen)$|(?:all|everything)\b)"
        r"(?:the |my )?(?P<app>.+?)(?: app| application| window)?(?: down| off)?"
        r"(?: for me| now| right now)?$",
        "close_app",
        Risk.SAFE,
    ),
    (
        "media_pause",
        r"^(?:pause|stop (?:the )?(?:music|song|playback|video)"
        r"|(?:put|keep) (?:the |my )?(?:music|song) on hold|hold (?:the |my )?(?:music|song))"
        r"(?: (?:the )?(?:music|song|video))?"
        rf"(?: (?:on|in) (?P<app>.+)|(?P<player> {_PLAYERS}))?$",
        "media",
        Risk.SAFE,
    ),
    (
        "media_play",
        rf"^(?:play|resume|unpause|continue)(?: (?:the )?(?:music|song|video|playback))?"
        rf"(?: (?:on|in) (?P<app>.+)|(?P<player> {_PLAYERS}))?$",
        "media",
        Risk.SAFE,
    ),
    (
        "media_next",
        rf"^(?:(?:play |go to |skip to )?(?:the )?next|skip(?: this)?)(?: (?:song|track|one))?"
        rf"(?: (?:on|in) (?P<app>.+)|(?P<player> {_PLAYERS}))?$",
        "media",
        Risk.SAFE,
    ),
    (
        "media_previous",
        rf"^(?:(?:play |go back to |go to )?(?:the )?(?:previous|last)|go back(?: a| one)?|back)"
        rf"(?: (?:song|track|one))?(?: (?:on|in) (?P<app>.+)|(?P<player> {_PLAYERS}))?$",
        "media",
        Risk.SAFE,
    ),
    ("open_app", r"^(?:open|launch|start) (?P<app>.+)$", "open_app", Risk.SAFE),
    ("search", r"^(?:search(?: the web)? for|google|look up) (?P<query>.+)$", "search", Risk.SAFE),
    (
        "volume_set",
        r"^(?:set |turn )?(?:the )?volume (?:to|at) (?P<level>\d{1,3})(?: percent)?$",
        "volume_set",
        Risk.SAFE,
    ),
    (
        "volume_up",
        r"^(?:(?:turn )?(?:the )?volume up|turn (?:it|the sound|the volume) up"
        r"|(?:a bit |a little )?louder|make it louder|raise the volume|up)$",
        "volume_up",
        Risk.SAFE,
    ),
    (
        "volume_down",
        r"^(?:(?:turn )?(?:the )?volume down|turn (?:it|the sound|the volume) down"
        r"|(?:a bit |a little )?quieter|make it quieter|lower the volume"
        r"|(?:it'?s |its )?(?:way |so |a bit |much )?too loud(?: in here)?|down)$",
        "volume_down",
        Risk.SAFE,
    ),
    ("mute", r"^(?:mute|unmute)(?: it| the sound| the volume| everything)?$", "mute", Risk.SAFE),
    ("lock", r"^lock(?: (?:the|my))?(?: screen| computer| pc| laptop)$", "lock", Risk.SAFE),
    ("screenshot", r"^(?:take |grab )?(?:a )?screen ?shot$", "screenshot", Risk.SAFE),
    (
        "battery",
        r"^(?:battery|battery level|how much battery(?: do i have| is left)?"
        r"|what'?s (?:my|the) battery(?: level)?)$",
        "battery",
        Risk.SAFE,
    ),
    (
        "time",
        r"^(?:what time is it|what'?s the time|what is the time|time"
        r"|what day is it|what'?s the date|what'?s today'?s date|what is the date)$",
        "time",
        Risk.SAFE,
    ),
    (
        "stop",
        r"^(?:stop|stop it|go to sleep|stop listening|never mind|nevermind|cancel"
        r"|that'?s all|that'?s it|nothing|no thanks)$",
        "stop",
        Risk.SAFE,
    ),
    ("help", r"^(?:help|what can you do)$", "help", Risk.SAFE),
)
