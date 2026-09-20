"""cti-confidence — confidence, corroboration and assessment primitives for CTI.

A small reference implementation of three things intelligence work needs and most
security tooling does not model:

1. **Two-axis source grading** (Admiralty Code) — source reliability and information
   credibility kept separate, because collapsing them destroys the information an
   analyst uses to decide whether to seek corroboration.
2. **Published estimative bands** (after ICD 203) — so "likely" means the same to
   writer and reader, and so confidence in the assessment stays distinct from the
   likelihood of the event.
3. **Three assessment states** — ``ASSESSED_TRUE``, ``ASSESSED_FALSE`` and
   ``UNABLE_TO_ASSESS``. The third is the one that is usually missing, and its
   absence is why "we did not look" gets reported as "we looked and found nothing".

Corroboration is counted by **independent origin**, so five aggregators republishing
one claim count as one piece of evidence rather than five.
"""

from .admiralty import AdmiraltyGrade, Credibility, Reliability
from .assessment import Assessment, Verdict, unable_to_assess
from .corroboration import Corroboration, Report, corroborate
from .estimative import AnalyticConfidence, Likelihood

__version__ = "0.1.0"

__all__ = [
    "AdmiraltyGrade",
    "AnalyticConfidence",
    "Assessment",
    "Corroboration",
    "Credibility",
    "Likelihood",
    "Reliability",
    "Report",
    "Verdict",
    "corroborate",
    "unable_to_assess",
]
