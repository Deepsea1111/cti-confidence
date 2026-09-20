"""A worked example: an indicator that looks corroborated and is not.

Run with:  python examples/worked_example.py
"""

from cti_confidence import (
    AdmiraltyGrade, AnalyticConfidence, Assessment, Likelihood,
    Report, Verdict, corroborate, unable_to_assess,
)

# Five reports of the same claim. Four are republications of the first.
C3 = AdmiraltyGrade.parse("C3")
reports = [
    Report("origin-blog", "origin-blog", C3, collected_at="2026-09-01T09:12:00Z"),
    Report("aggregator-a", "origin-blog", C3, collected_at="2026-09-01T14:40:00Z"),
    Report("aggregator-b", "origin-blog", C3, collected_at="2026-09-02T06:03:00Z"),
    Report("newsletter-c", "origin-blog", C3, collected_at="2026-09-02T11:55:00Z"),
    Report("vendor-feed-d", "origin-blog", C3, collected_at="2026-09-03T02:20:00Z"),
]

corr = corroborate(reports)
print("naive count :", corr.report_count, "reports")
print("honest count:", corr.independent_origins, "independent origin(s)")
print("inflation   :", f"{corr.inflation_factor:.1f}x")
print()

# With one origin at C3, "confirmed" is not available to us.
assessment = Assessment(
    claim="203.0.113.10 is dedicated C2 infrastructure for the actor tracked as X",
    verdict=Verdict.ASSESSED_TRUE,
    likelihood=Likelihood.UNLIKELY,
    confidence=AnalyticConfidence.LOW,
    corroboration=corr,
    falsifier="a second, independently originated report, or passive DNS showing "
              "the address in shared hosting during the window",
)
print(assessment.line())
print()

# And the state most tooling cannot express.
gap = unable_to_assess(
    claim="Did this address contact our estate during the reporting window?",
    reason="netflow retention is 7 days; the window is 30 days old",
)
print(gap.line())
