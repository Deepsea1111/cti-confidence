"""Assessments with three states and a mandatory falsifier.

Two design decisions carry this module.

**Three states, not two.** Most tooling supports *confirmed* and *not confirmed*,
which is one state short. There are three:

============================  ===========================================
``ASSESSED_TRUE``             we looked and formed a judgement
``ASSESSED_FALSE``            we looked and the evidence is against it
``UNABLE_TO_ASSESS``          we did not look, could not look, or the
                              evidence does not bear on the question
============================  ===========================================

``UNABLE_TO_ASSESS`` is **not** low confidence. Low confidence is a judgement;
this is the absence of one. A schema with nowhere to put it will store it as a
negative finding — and "we did not look" and "we looked and found nothing" are
opposite claims. Any pipeline that conflates them generates false negatives at a
rate it cannot measure, because the records that would reveal the rate are the ones
being silently converted.

**The falsifier is mandatory.** An assessment that cannot name the observation that
would overturn it was not reasoned to; it was arrived at. Making the field required
is the cheapest available forcing function, so :class:`Assessment` refuses to be
constructed without one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .corroboration import Corroboration
from .estimative import AnalyticConfidence, Likelihood

__all__ = ["Verdict", "Assessment", "unable_to_assess"]


class Verdict(str, Enum):
    ASSESSED_TRUE = "assessed_true"
    ASSESSED_FALSE = "assessed_false"
    UNABLE_TO_ASSESS = "unable_to_assess"

    @property
    def is_judgement(self) -> bool:
        """False only for ``UNABLE_TO_ASSESS``.

        Use this rather than truthiness tests anywhere a caller is tempted to write
        ``if verdict == ASSESSED_TRUE: ... else: ...``, which quietly folds
        "we could not tell" into "we assessed it false".
        """
        return self is not Verdict.UNABLE_TO_ASSESS


@dataclass(frozen=True, slots=True)
class Assessment:
    """A single assessment about one claim.

    Args:
        claim: What is being assessed, stated plainly.
        verdict: One of the three states above.
        falsifier: The observation that would overturn this assessment. Required for
            a judgement; for ``UNABLE_TO_ASSESS`` it is replaced by ``reason``.
        likelihood: Estimative band, when a judgement was made.
        confidence: Confidence in the assessment itself (about the evidence).
        corroboration: Independent-origin count behind the assessment.
        reason: Why no judgement could be made. Required for ``UNABLE_TO_ASSESS``
            and rejected otherwise, so that the field cannot be used to smuggle a
            caveat into a judgement.
    """

    claim: str
    verdict: Verdict
    falsifier: str | None = None
    likelihood: Likelihood | None = None
    confidence: AnalyticConfidence | None = None
    corroboration: Corroboration | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.claim.strip():
            raise ValueError("claim must not be empty")

        if self.verdict.is_judgement:
            if not (self.falsifier or "").strip():
                raise ValueError(
                    "a judgement requires a falsifier: name the observation that "
                    "would overturn it"
                )
            if self.confidence is None:
                raise ValueError("a judgement requires an analytic confidence")
            if self.reason is not None:
                raise ValueError(
                    "'reason' describes why no judgement was possible and cannot "
                    "accompany a judgement; put caveats in the falsifier or the claim"
                )
        else:
            if not (self.reason or "").strip():
                raise ValueError(
                    "UNABLE_TO_ASSESS requires a reason: say what was not looked at, "
                    "and why"
                )
            if self.likelihood is not None or self.confidence is not None:
                raise ValueError(
                    "UNABLE_TO_ASSESS carries no likelihood or confidence — it is the "
                    "absence of a judgement, not a low one"
                )

    def line(self) -> str:
        """One-line rendering suitable for a report or a log."""
        if not self.verdict.is_judgement:
            return f"[unable to assess] {self.claim} — {self.reason}"
        bits = [f"[{self.verdict.value}] {self.claim}"]
        if self.likelihood is not None:
            bits.append(f"{self.likelihood.value}")
        if self.confidence is not None:
            bits.append(f"{self.confidence.value} confidence")
        if self.corroboration is not None:
            bits.append(self.corroboration.summary())
        return " · ".join(bits) + f" · overturned by: {self.falsifier}"


def unable_to_assess(claim: str, reason: str) -> Assessment:
    """Convenience constructor for the state people forget to model."""
    return Assessment(claim=claim, verdict=Verdict.UNABLE_TO_ASSESS, reason=reason)
