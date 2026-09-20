"""Estimative language with fixed, published probability bands.

Words like "possible" and "probable" are read at wildly different probabilities by
different people. An intelligence function that has not fixed their meaning is
miscommunicating at a rate it has no way to measure, because both writer and reader
believe they understood each other.

The bands here follow the structure of US ODNI Intelligence Community Directive 203
(*Analytic Standards*). What matters is far less which bands you pick than that they
are **published, fixed, and applied consistently** — so `from_probability` and
`Likelihood.band` are deliberately exact and total: every probability in [0, 1] maps
to exactly one band, with no gaps and no overlap.

Separately from likelihood, ICD 203 distinguishes *confidence in the assessment*,
which is a statement about the evidence rather than about the event. The two are
independent: one can be highly confident that an event is unlikely. They are modelled
here as separate types for that reason.
"""

from __future__ import annotations

from enum import Enum

__all__ = ["Likelihood", "AnalyticConfidence"]


class Likelihood(str, Enum):
    """How likely the event is, expressed on fixed bands.

    Bands are contiguous and half-open on the upper edge except the last, so that every
    probability belongs to exactly one band.
    """

    ALMOST_NO_CHANCE = "almost no chance"
    VERY_UNLIKELY = "very unlikely"
    UNLIKELY = "unlikely"
    ROUGHLY_EVEN_CHANCE = "roughly even chance"
    LIKELY = "likely"
    VERY_LIKELY = "very likely"
    ALMOST_CERTAIN = "almost certain"

    @property
    def band(self) -> tuple[float, float]:
        """Inclusive-lower, exclusive-upper probability band (last band includes 1.0)."""
        return _BANDS[self]

    @classmethod
    def from_probability(cls, p: float) -> "Likelihood":
        """Map a probability to its band.

        Raises:
            ValueError: if *p* is outside [0, 1]. An out-of-range probability is a
                defect in the caller, not a value to be clamped — clamping would
                convert a bug into a plausible-looking assessment.
        """
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"probability must be in [0, 1], got {p!r}")
        for level, (low, high) in _BANDS.items():
            if low <= p < high or (p == 1.0 and high == 1.0):
                return level
        raise AssertionError(f"bands do not cover {p!r}")  # pragma: no cover


#: Ordered low → high. Contiguous by construction; see ``test_bands_are_total``.
_BANDS: dict[Likelihood, tuple[float, float]] = {
    Likelihood.ALMOST_NO_CHANCE: (0.00, 0.05),
    Likelihood.VERY_UNLIKELY: (0.05, 0.20),
    Likelihood.UNLIKELY: (0.20, 0.45),
    Likelihood.ROUGHLY_EVEN_CHANCE: (0.45, 0.55),
    Likelihood.LIKELY: (0.55, 0.80),
    Likelihood.VERY_LIKELY: (0.80, 0.95),
    Likelihood.ALMOST_CERTAIN: (0.95, 1.00),
}


class AnalyticConfidence(str, Enum):
    """Confidence in the *assessment*, which is a claim about the evidence.

    Orthogonal to :class:`Likelihood`. "We assess with high confidence that this is
    very unlikely" is a coherent and common statement; conflating the two axes makes
    it inexpressible.
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"

    @property
    def basis(self) -> str:
        return _CONFIDENCE_BASIS[self]


_CONFIDENCE_BASIS: dict[AnalyticConfidence, str] = {
    AnalyticConfidence.LOW: (
        "scant, questionable or fragmented evidence; plausible alternative "
        "hypotheses remain open"
    ),
    AnalyticConfidence.MODERATE: (
        "credible evidence from sources of varying reliability, but not corroborated "
        "well enough to close out alternatives"
    ),
    AnalyticConfidence.HIGH: (
        "high-quality evidence from multiple sources of independent origin; "
        "alternative hypotheses have been considered and can be largely discounted"
    ),
}
