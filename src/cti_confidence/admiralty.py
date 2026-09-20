"""Admiralty Code — source reliability and information credibility, kept separate.

The grading system used here follows NATO STANAG 2511 (also called the NATO System
or the Admiralty System). Its defining property, and the only reason this module
exists as something other than a lookup table, is that it grades **two independent
axes**:

* how reliable the *source* has proven to be, and
* how credible *this particular claim* is.

Collapsing them into a single "confidence score" — which most tooling does —
destroys the distinction that tells an analyst what to do next. A completely
reliable source can report something improbable (A5), and an unreliable source can
be right (E1). Those two situations call for opposite responses: the first wants
corroboration of the content, the second wants corroboration of the source. A
single blended number cannot express either.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = ["Reliability", "Credibility", "AdmiraltyGrade"]


class Reliability(str, Enum):
    """Axis 1 — the track record of the source.

    This is a judgement about the *source*, accumulated over time. It is not a
    judgement about the report in hand.
    """

    COMPLETELY_RELIABLE = "A"
    USUALLY_RELIABLE = "B"
    FAIRLY_RELIABLE = "C"
    NOT_USUALLY_RELIABLE = "D"
    UNRELIABLE = "E"
    #: No basis exists to judge the source. ⚠️ This is *not* a low grade — it is the
    #: absence of a grade. Treating F as "bad" is the single most common misuse of
    #: this scale, because it silently converts "we do not know" into "we assess badly".
    CANNOT_BE_JUDGED = "F"

    @property
    def is_judgeable(self) -> bool:
        return self is not Reliability.CANNOT_BE_JUDGED

    @property
    def label(self) -> str:
        return _RELIABILITY_LABELS[self]


class Credibility(str, Enum):
    """Axis 2 — the plausibility of *this* claim, assessed on its own merits.

    Judged against other holdings and against what is known to be true, and
    deliberately independent of who reported it.
    """

    CONFIRMED = "1"
    PROBABLY_TRUE = "2"
    POSSIBLY_TRUE = "3"
    DOUBTFUL = "4"
    IMPROBABLE = "5"
    #: The content cannot be assessed at all. As with ``Reliability.CANNOT_BE_JUDGED``
    #: this is the absence of a judgement, not a negative one.
    CANNOT_BE_JUDGED = "6"

    @property
    def is_judgeable(self) -> bool:
        return self is not Credibility.CANNOT_BE_JUDGED

    @property
    def label(self) -> str:
        return _CREDIBILITY_LABELS[self]


_RELIABILITY_LABELS: dict[Reliability, str] = {
    Reliability.COMPLETELY_RELIABLE: "completely reliable",
    Reliability.USUALLY_RELIABLE: "usually reliable",
    Reliability.FAIRLY_RELIABLE: "fairly reliable",
    Reliability.NOT_USUALLY_RELIABLE: "not usually reliable",
    Reliability.UNRELIABLE: "unreliable",
    Reliability.CANNOT_BE_JUDGED: "reliability cannot be judged",
}

_CREDIBILITY_LABELS: dict[Credibility, str] = {
    Credibility.CONFIRMED: "confirmed by other sources",
    Credibility.PROBABLY_TRUE: "probably true",
    Credibility.POSSIBLY_TRUE: "possibly true",
    Credibility.DOUBTFUL: "doubtful",
    Credibility.IMPROBABLE: "improbable",
    Credibility.CANNOT_BE_JUDGED: "credibility cannot be judged",
}


@dataclass(frozen=True, slots=True)
class AdmiraltyGrade:
    """A two-axis grade, e.g. ``B2``.

    Deliberately offers no ``score`` property, no ordering, and no arithmetic. A
    grade of ``A5`` is not "better" or "worse" than ``D1``; they describe different
    situations requiring different follow-up. Any function that reduces this to one
    number is discarding the reason the scale has two axes, so this class refuses to
    provide one.
    """

    reliability: Reliability
    credibility: Credibility

    @classmethod
    def parse(cls, code: str) -> "AdmiraltyGrade":
        """Parse a two-character code such as ``"B2"`` (case-insensitive)."""
        raw = code.strip().upper()
        if len(raw) != 2:
            raise ValueError(f"Admiralty code must be exactly two characters, got {code!r}")
        try:
            return cls(Reliability(raw[0]), Credibility(raw[1]))
        except ValueError as exc:  # pragma: no cover - message construction only
            raise ValueError(f"not a valid Admiralty code: {code!r}") from exc

    @property
    def code(self) -> str:
        return f"{self.reliability.value}{self.credibility.value}"

    @property
    def is_fully_judgeable(self) -> bool:
        """True only when *both* axes carry an actual judgement."""
        return self.reliability.is_judgeable and self.credibility.is_judgeable

    def describe(self) -> str:
        return f"{self.code} — {self.reliability.label}; {self.credibility.label}"

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.code
