import pytest

from cti_confidence import (
    AdmiraltyGrade, AnalyticConfidence, Assessment, Likelihood,
    Report, Verdict, corroborate, unable_to_assess,
)


def judgement(**kw):
    base = dict(
        claim="Infrastructure 185.x is operated by the actor tracked as X",
        verdict=Verdict.ASSESSED_TRUE,
        falsifier="the address is shown to be a shared CDN edge during the window",
        likelihood=Likelihood.LIKELY,
        confidence=AnalyticConfidence.MODERATE,
    )
    base.update(kw)
    return Assessment(**base)


# ── the three states are genuinely three ──────────────────────────────────────

def test_unable_to_assess_is_not_a_judgement():
    a = unable_to_assess("Was the payroll system accessed?", "logs not retained for the window")
    assert a.verdict is Verdict.UNABLE_TO_ASSESS
    assert not a.verdict.is_judgement
    assert a.likelihood is None and a.confidence is None


def test_assessed_false_is_a_judgement_not_an_absence():
    a = judgement(verdict=Verdict.ASSESSED_FALSE, likelihood=Likelihood.VERY_UNLIKELY)
    assert a.verdict.is_judgement
    assert a.verdict is not Verdict.UNABLE_TO_ASSESS


def test_all_three_states_are_distinct():
    assert len({v for v in Verdict}) == 3


# ── the guards must actually fire ─────────────────────────────────────────────

def test_judgement_without_falsifier_is_rejected():
    with pytest.raises(ValueError, match="falsifier"):
        judgement(falsifier=None)


def test_whitespace_falsifier_is_rejected():
    """A space is not a falsifier; the check must look at content, not presence."""
    with pytest.raises(ValueError, match="falsifier"):
        judgement(falsifier="   ")


def test_judgement_without_confidence_is_rejected():
    with pytest.raises(ValueError, match="confidence"):
        judgement(confidence=None)


def test_unable_to_assess_without_reason_is_rejected():
    with pytest.raises(ValueError, match="reason"):
        Assessment(claim="x", verdict=Verdict.UNABLE_TO_ASSESS)


def test_unable_to_assess_cannot_carry_confidence():
    """It is the absence of a judgement, not a low-confidence one."""
    with pytest.raises(ValueError, match="absence of a judgement"):
        Assessment(
            claim="x", verdict=Verdict.UNABLE_TO_ASSESS, reason="not collected",
            confidence=AnalyticConfidence.LOW,
        )


def test_judgement_cannot_smuggle_a_reason():
    with pytest.raises(ValueError, match="cannot"):
        judgement(reason="we were a bit unsure")


def test_empty_claim_is_rejected():
    with pytest.raises(ValueError, match="claim"):
        judgement(claim="  ")


# ── rendering ─────────────────────────────────────────────────────────────────

def test_line_states_the_falsifier():
    line = judgement().line()
    assert "overturned by" in line
    assert "likely" in line
    assert "moderate confidence" in line


def test_unable_line_says_what_was_not_looked_at():
    line = unable_to_assess("Was X accessed?", "logs not retained").line()
    assert "unable to assess" in line
    assert "logs not retained" in line
    assert "confidence" not in line


def test_corroboration_summary_travels_with_the_assessment():
    grade = AdmiraltyGrade.parse("B2")
    corr = corroborate([
        Report("vendor-a", "vendor-a", grade),
        Report("aggregator", "vendor-a", grade),
    ])
    line = judgement(corroboration=corr).line()
    assert "1 independent origin(s) from 2 report(s)" in line
    assert "1 circular" in line


def test_assessment_is_immutable():
    a = judgement()
    with pytest.raises(Exception):
        a.claim = "something else"  # type: ignore[misc]
