# cti-confidence

Confidence, corroboration and assessment primitives for cyber threat intelligence.

A small, dependency-free reference implementation of three things intelligence work
needs and most security tooling does not model:

1. **Two-axis source grading** — Admiralty Code (NATO STANAG 2511), with source
   reliability and information credibility kept separate.
2. **Published estimative bands** — after ICD 203, so *likely* means the same thing to
   the writer and the reader, and confidence in the assessment stays distinct from the
   likelihood of the event.
3. **Three assessment states** — because `confirmed` / `not confirmed` is one state
   short, and the missing one is the expensive one.

Corroboration is counted by **independent origin**, so five aggregators republishing a
single claim count as one piece of evidence rather than five.

```bash
pip install git+https://github.com/Deepsea1111/cti-confidence
```

Requires Python 3.11+. No runtime dependencies.
Not yet on PyPI — install from source, or clone and `pip install -e ".[dev]"`.

---

## Why this exists

Most confidence handling in security tooling fails in one of four ways. This library is
shaped by those four failures; each one is a design constraint rather than a feature.

### 1. Collapsing two axes into one number

A "confidence score" of `0.87` tells you nothing about *why*. The Admiralty Code grades
source reliability (`A`–`F`) and information credibility (`1`–`6`) separately, because
they call for different responses:

| Grade | Situation | What to do about it |
| --- | --- | --- |
| `A5` | Completely reliable source reporting something improbable | Corroborate the **content** |
| `E1` | Unreliable source reporting something confirmed elsewhere | Corroborate the **source** |
| `B2` | Usually reliable source, probably true content | Usable; note the residual |

A single blended number cannot express either of the first two. So `AdmiraltyGrade`
deliberately exposes **no** `score`, supports no ordering, and permits no arithmetic —
and there is a test asserting it stays that way.

### 2. Counting reports instead of origins

Circular reporting is the most common way open-source confidence inflates without any
new evidence existing. One blog post, republished by four aggregators, arrives looking
like five sources agreeing.

```python
from cti_confidence import AdmiraltyGrade, Report, corroborate

grade = AdmiraltyGrade.parse("C3")
reports = [
    Report("origin-blog",   "origin-blog", grade),
    Report("aggregator-a",  "origin-blog", grade),
    Report("aggregator-b",  "origin-blog", grade),
    Report("newsletter-c",  "origin-blog", grade),
    Report("vendor-feed-d", "origin-blog", grade),
]

result = corroborate(reports)
print(result.summary())
# 1 independent origin(s) from 5 report(s); 4 circular
print(result.inflation_factor)
# 5.0
```

Independence is a property of **origin**, not of publication and not of analysis. Two
findings produced by different analysts from the same sandbox report are one finding
examined twice.

`corroborate()` returns counts, not a confidence value. How many independent origins
justify what level of confidence is an analytic judgement that depends on the claim and
on the cost of being wrong — not something a library should decide for you. Handing back
a number there would be exactly the invented precision this package exists to discourage.

### 3. Unstandardised estimative language

"Possible" and "probable" are read at wildly different probabilities by different people.
An organisation that has not fixed their meanings is miscommunicating at a rate it cannot
measure, because both parties believe they understood each other.

```python
from cti_confidence import Likelihood

Likelihood.from_probability(0.70)   # <Likelihood.LIKELY>
Likelihood.LIKELY.band              # (0.55, 0.8)
Likelihood.from_probability(1.5)    # ValueError — not clamped
```

Bands are contiguous, half-open, and total over `[0, 1]`: every probability maps to
exactly one band, with no gaps and no overlap. Out-of-range input raises rather than
clamps, because clamping converts a caller's bug into a plausible-looking assessment.

Likelihood and confidence are separate types. *"We assess with high confidence that this
is very unlikely"* is a coherent and common statement; conflating the axes makes it
inexpressible.

### 4. Two assessment states where there are three

| State | Meaning |
| --- | --- |
| `ASSESSED_TRUE` | We looked, and formed a judgement |
| `ASSESSED_FALSE` | We looked, and the evidence is against it |
| `UNABLE_TO_ASSESS` | We did not look, could not look, or the evidence does not bear on it |

**`UNABLE_TO_ASSESS` is not low confidence.** Low confidence is a judgement; this is the
absence of one. A schema with nowhere to put it will store it as a negative finding — and
*"we did not look"* and *"we looked and found nothing"* are opposite claims. Any pipeline
that conflates them generates false negatives at a rate it cannot measure, because the
records that would reveal the rate are the ones being silently converted.

```python
from cti_confidence import unable_to_assess

a = unable_to_assess(
    claim="Was the payroll system accessed during the window?",
    reason="authentication logs are not retained beyond 14 days",
)
print(a.line())
# [unable to assess] Was the payroll system accessed during the window? —
# authentication logs are not retained beyond 14 days
```

---

## The falsifier is mandatory

An assessment that cannot name the observation that would overturn it was not reasoned
to; it was arrived at. `Assessment` refuses to be constructed without one:

```python
from cti_confidence import (
    Assessment, Verdict, Likelihood, AnalyticConfidence,
    AdmiraltyGrade, Report, corroborate,
)

grade = AdmiraltyGrade.parse("B2")
corr = corroborate([
    Report("vendor-a", "vendor-a", grade),
    Report("own-telemetry", "own-telemetry", grade),
])

a = Assessment(
    claim="185.x is dedicated infrastructure operated by the actor tracked as X",
    verdict=Verdict.ASSESSED_TRUE,
    likelihood=Likelihood.LIKELY,
    confidence=AnalyticConfidence.MODERATE,
    corroboration=corr,
    falsifier="the address is shown to be a shared CDN edge during the window",
)
print(a.line())
```

```
[assessed_true] 185.x is dedicated infrastructure operated by the actor tracked as X ·
likely · moderate confidence · 2 independent origin(s) from 2 report(s) ·
overturned by: the address is shown to be a shared CDN edge during the window
```

Omit the falsifier and construction fails:

```python
Assessment(claim="...", verdict=Verdict.ASSESSED_TRUE,
           likelihood=Likelihood.LIKELY, confidence=AnalyticConfidence.MODERATE)
# ValueError: a judgement requires a falsifier: name the observation that would overturn it
```

---

## Design notes

**The guards are tested to fire.** A validation rule that has never been observed to
reject anything is indistinguishable from one that is not running. Every constraint in
this library has a test that asserts the rejection, not only a test that asserts the
happy path.

**Nothing here invents precision.** No function returns a confidence value the caller
did not supply. No grade has a numeric score. No corroboration count is converted into a
recommendation. Where a judgement is required, the library requires the caller to make
it and to record what would overturn it.

**Timestamps are opaque strings.** `Report.collected_at` is stored and never parsed or
compared. A library with no business reasoning about time should not acquire timezone
bugs by pretending otherwise.

**Unknown is never a default.** `CANNOT_BE_JUDGED` on either Admiralty axis means *no
basis exists to judge*, not *judged badly*. `is_fully_judgeable` exists so callers can
branch on that explicitly instead of discovering it by accident.

---

## Testing

```bash
pip install -e ".[dev]"
pytest
```

---

## Further reading

The reasoning behind these choices is written up at
[wiboonnissara.com](https://wiboonnissara.com):

- [OSINT, Attribution, and the Honest Expression of Confidence](https://wiboonnissara.com/articles/osint-attribution-confidence)
- [What Is Cyber Threat Intelligence?](https://wiboonnissara.com/articles/what-is-cyber-threat-intelligence)
- [From OSINT Collection to Actionable Cyber Threat Intelligence](https://wiboonnissara.com/research/osint-to-actionable-cti)
- [Measuring Blind Spots in Intelligence Collection](https://wiboonnissara.com/research/measuring-blind-spots)

Primary sources:

- NATO STANAG 2511 — Admiralty Code / NATO System
- US ODNI **Intelligence Community Directive 203**, *Analytic Standards*
- Richards J. Heuer Jr., *Psychology of Intelligence Analysis* (CIA CSI, 1999)

---

## Status and scope

Alpha. The API is small on purpose and may still change before `1.0`.

This library models *how a judgement is expressed and recorded*. It does not collect,
does not enrich, does not score indicators, and will not tell you whether something is
malicious. Those are different problems, and mixing them in would undermine the one
property this package is for: that every number it carries can be traced to a person who
decided it.

## Licence

MIT — see [LICENSE](LICENSE).
