"""Turns a spoken explanation into a polished document, and revises it on request.

Speech is messy: people think aloud, repeat themselves, correct themselves and leave things
implicit, and speech recognition mishears words. The writer's job is to work out what the
speaker meant and write that well, without adding facts they never gave.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from hi_puter.brain.llm import ChatModel, Message
from hi_puter.core.errors import ModelError

log = logging.getLogger("hi_puter")

WRITE_TIMEOUT_SECONDS = 900.0  # a full document on a laptop CPU can take several minutes
MAX_DOCUMENT_TOKENS = 1800  # about 1,300 words; keeps writing and revising inside the context
MAX_DICTATION_CHARS = 6000  # about 1,500 tokens of what the user said
MIN_DOCUMENT_WORDS = 5  # anything shorter means the model returned nothing useful

KINDS = {
    "document": "document",
    "doc": "document",
    "letter": "letter",
    "cover letter": "cover letter",
    "email": "email",
    "e-mail": "email",
    "essay": "essay",
    "report": "report",
    "article": "article",
    "blog post": "blog post",
    "memo": "memo",
    "proposal": "proposal",
    "story": "story",
    "speech": "speech",
    "summary": "summary",
}

WRITER_RULES = """\
You are an expert writer and editor. The user explained out loud what they want written. \
You get a speech-to-text transcript, so expect filler words, repetition, self-corrections, \
half-finished thoughts and misheard words. Your job is to understand what they meant and \
turn it into a polished {kind} that says it well.

Faithfulness
- Keep every point, fact, name, date, number and request the user gave. Leave nothing out.
- Never invent facts, names, figures, quotes or commitments, and never exaggerate. Do not \
add urgency, severity, emotion or descriptive words the user did not express: "drips when \
it rains" must not become "leaks constantly", and "please fix it this week" must not become \
"urgent" or "critical". Where a detail is missing, \
write around it naturally; only if the {kind} cannot work without it (such as a recipient's \
name or a date), use a clear placeholder in square brackets, like [Recipient name].
- When the user corrects themselves ("no wait, I mean Tuesday"), use the correction.
- Fix words the speech recognition obviously misheard, using the context.

Form
- Follow the conventions of a {kind}: a letter has a greeting, body paragraphs and a \
sign-off, with no "To:", "Date:" or "Subject:" lines and no bold text; an email has a \
"Subject:" line, greeting and sign-off; a report or proposal has short headings; an essay or \
article has an introduction, a clear argument and a conclusion; a story has a narrative arc.
- Order the ideas logically, even if the user said them out of order.
- Use headings, numbered steps or bullet points only where they make the content easier to \
read. Prefer well-built paragraphs.

Style
- Write clear, specific, confident prose: active voice, concrete words, varied sentence \
length, short paragraphs.
- Cut filler, repetition, hedging and cliches. Every sentence should earn its place.
- Match the tone the user asks for exactly ("polite but firm" means calm, courteous and \
direct, not alarmed); if they didn't say, use a warm professional tone for letters \
and emails and a clear neutral tone otherwise. Keep tone, tense and person consistent.
- Use correct grammar, spelling and punctuation, in the same language the user spoke.

Output
- Output only the finished {kind} in Markdown, starting with a "# " title line.
- No notes, explanations or questions before or after it.
"""

REVISE_RULES = """\
You are an expert editor. Below is a document the user had written, followed by their \
spoken instruction for changing it (a speech-to-text transcript, so read it for intent). \
Apply the instruction to the whole document.

- "Shorter" means substantially shorter: cut at least a third of the words by removing \
repetition and less important detail, not just one sentence. "Longer" means developing the \
existing points, never inventing new facts.
- When you remove something, also remove any heading or sentence that only introduced it.
- Change only what the instruction asks for; keep everything else, including facts, names \
and structure, unless the instruction is about them.
- Never invent facts. Keep the document's form and its "# " title line.
- Keep the writing clear, tight and correct.
- Output only the complete revised document in Markdown, with no notes before or after it.
"""


@dataclass(frozen=True)
class DocumentRequest:
    kind: str = "document"
    topic: str = ""


@dataclass(frozen=True)
class Document:
    path: Path
    title: str
    words: int
    kind: str


def topic_phrase(topic: str) -> str:
    """ "to my landlord about rent" -> " to my landlord about rent"; "rent" -> " about rent"."""
    topic = topic.strip()
    if not topic:
        return ""
    first = topic.split()[0].lower()
    joined = first in {"about", "on", "for", "to", "regarding", "thanking", "asking", "telling"}
    return f" {topic}" if joined else f" about {topic}"


def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def document_kind(spoken: str) -> str:
    return KINDS.get(spoken.strip().lower(), "document")


def clean_markdown(text: str) -> str:
    """Strip reasoning, code fences and chatter around the document; ensure a title."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    fenced = re.fullmatch(r"```(?:markdown|md)?\s*\n(.*?)\n?```", text, flags=re.S)
    if fenced:
        text = fenced.group(1).strip()
    title_at = re.search(r"^# \S", text, flags=re.M)
    if title_at:
        text = text[title_at.start() :]  # drop "Sure, here is your letter:" and the like
    elif text:
        first, _, rest = text.partition("\n")
        text = f"# {first.strip('#* ').strip()}\n{rest}".strip()
    return text.strip() + "\n"


MEMO_HEADER = re.compile(r"^\s*\**\s*(?:to|from|date|subject|re)\s*:.*$\n?", re.I | re.M)


def tidy_for(kind: str, markdown: str) -> str:
    """Conventions small models often break, fixed in code rather than hoped for.

    Letters get no memo-style To/Date/Subject lines and no bold; emails keep a plain
    "Subject:" line but lose bold.
    """
    if kind in {"letter", "cover letter"}:
        markdown = MEMO_HEADER.sub("", markdown)
    if kind in {"letter", "cover letter", "email"}:
        markdown = re.sub(r"\*\*(.+?)\*\*", r"\1", markdown)
        markdown = re.sub(r"^\*\s+(?=\S)", "- ", markdown, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", markdown).strip() + "\n"


def title_of(markdown: str) -> str:
    found = re.search(r"^# (.+)$", markdown, flags=re.M)
    return re.sub(r"[*_`]", "", found.group(1)).strip() if found else "Untitled"


def safe_filename(title: str) -> str:
    name = re.sub(r"[^\w\s.,'()-]", "", title).strip(" .")
    return re.sub(r"\s+", " ", name)[:80] or "Untitled"


class Writer:
    def __init__(
        self,
        model: ChatModel,
        folder: Path,
        *,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        self.model = model
        self.folder = folder
        self.clock = clock
        self.last: Document | None = None

    def write(self, dictation: str, request: DocumentRequest) -> Document:
        said = " ".join(dictation.split())[:MAX_DICTATION_CHARS]
        if not said:
            raise ValueError("nothing was dictated")
        kind = request.kind or "document"
        intro = f"Write {article(kind)} {kind}{topic_phrase(request.topic)}"
        messages: list[Message] = [
            {"role": "system", "content": WRITER_RULES.format(kind=kind)},
            {"role": "user", "content": f"{intro}. Here is what I said:\n\n{said}"},
        ]
        markdown = tidy_for(kind, self._generate(messages))
        return self._save(markdown, kind, replace=None)

    def revise(self, instruction: str) -> Document:
        if self.last is None:
            raise ValueError("there is no document to change yet")
        current = self.last.path.read_text(encoding="utf-8")
        messages: list[Message] = [
            {"role": "system", "content": REVISE_RULES},
            {
                "role": "user",
                "content": f"Document:\n\n{current}\n\nInstruction: {instruction.strip()}",
            },
        ]
        markdown = tidy_for(self.last.kind, self._generate(messages))
        return self._save(markdown, self.last.kind, replace=self.last.path)

    def _generate(self, messages: list[Message]) -> str:
        reply = self.model.chat(
            messages, [], timeout=WRITE_TIMEOUT_SECONDS, max_tokens=MAX_DOCUMENT_TOKENS
        )
        markdown = clean_markdown(reply.content)
        if len(markdown.split()) < MIN_DOCUMENT_WORDS:
            raise ModelError("The language model returned an empty document.")
        return markdown

    def _save(self, markdown: str, kind: str, replace: Path | None) -> Document:
        title = title_of(markdown)
        if replace is not None:
            path = replace  # revisions update the same file
        else:
            self.folder.mkdir(parents=True, exist_ok=True)
            base = f"{self.clock():%Y-%m-%d} {safe_filename(title)}"
            path = self.folder / f"{base}.md"
            number = 2
            while path.exists():
                path = self.folder / f"{base} ({number}).md"
                number += 1
        path.write_text(markdown, encoding="utf-8")
        words = len(re.findall(r"\w+", re.sub(r"^#.*$", "", markdown, count=1, flags=re.M)))
        document = Document(path, title, words, kind)
        self.last = document
        log.info("Saved %s %r (%d words) to %s", kind, title, words, path)
        return document
