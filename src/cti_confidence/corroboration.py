"""Corroboration counted by independent origin, not by number of reports.

The most common way open-source confidence inflates is circular reporting: one
original claim is republished by five aggregators and arrives looking like five
sources agreeing. Nothing new was learned, but every naive corroboration count says
otherwise.

The rule this module enforces is blunt:

    **Two reports that trace to the same origin are one piece of evidence.**

Independence is a property of *origin*, not of publication and not of analysis. Two
findings produced by different analysts from the same sandbox report are one finding
examined twice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .admiralty import AdmiraltyGrade

__all__ = ["Report", "Corroboration", "corroborate"]


@dataclass(frozen=True, slots=True)
class Report:
    """One report of a claim.

    Args:
        source_id: Who handed us this report — the immediate source.
        origin_id: The earliest origin reachable for the claim. When a report is
            itself the origin, set this equal to ``source_id``. When the report is a
            republication, set it to the upstream origin so the copy stops counting
            as new evidence.
        grade: Admiralty grade for this report.
        collected_at: Free-form timestamp string, kept opaque on purpose — this
            library does not parse or compare times, and pretending otherwise would
            invite timezone bugs into a module that has no business having them.
    """

    source_id: str
    origin_id: str
    grade: AdmiraltyGrade
    collected_at: str | None = None

    @property
    def is_original(self) -> bool:
        return self.source_id == self.origin_id


@dataclass(frozen=True, slots=True)
class Corroboration:
    """The result of counting reports by origin.

    Attributes:
        independent_origins: Number of distinct origins — the honest corroboration count.
        report_count: Number of reports seen, including copies.
        circular_reports: Reports discarded as copies of an origin already counted.
        origins: The distinct origin identifiers, in first-seen order.
        unjudgeable_origins: Origins whose every report had an unjudgeable grade.
            Reported separately so that "we have three origins, two of which we cannot
            grade" is never flattened into "we have three origins".
    """

    independent_origins: int
    report_count: int
    circular_reports: int
    origins: tuple[str, ...] = field(default_factory=tuple)
    unjudgeable_origins: tuple[str, ...] = field(default_factory=tuple)

    @property
    def inflation_factor(self) -> float:
        """How much a naive count would have overstated corroboration.

        ``1.0`` means every report was independent. ``5.0`` means five reports
        collapsed to one origin.
        """
        if self.independent_origins == 0:
            return 0.0
        return self.report_count / self.independent_origins

    def summary(self) -> str:
        parts = [
            f"{self.independent_origins} independent origin(s) "
            f"from {self.report_count} report(s)"
        ]
        if self.circular_reports:
            parts.append(f"{self.circular_reports} circular")
        if self.unjudgeable_origins:
            parts.append(f"{len(self.unjudgeable_origins)} origin(s) ungradeable")
        return "; ".join(parts)


def corroborate(reports: list[Report]) -> Corroboration:
    """Count corroboration by independent origin.

    Deliberately does **not** return a confidence value. How many independent origins
    justify what level of confidence is an analytic judgement that depends on the
    claim, the domain, and the cost of being wrong — not something a library can
    decide on the caller's behalf. Handing back a number here would be exactly the
    kind of invented precision this package exists to discourage.
    """
    origins: list[str] = []
    seen: set[str] = set()
    graded_origins: set[str] = set()
    circular = 0

    for report in reports:
        if report.origin_id in seen:
            circular += 1
        else:
            seen.add(report.origin_id)
            origins.append(report.origin_id)
        if report.grade.is_fully_judgeable:
            graded_origins.add(report.origin_id)

    unjudgeable = tuple(o for o in origins if o not in graded_origins)

    return Corroboration(
        independent_origins=len(origins),
        report_count=len(reports),
        circular_reports=circular,
        origins=tuple(origins),
        unjudgeable_origins=unjudgeable,
    )
