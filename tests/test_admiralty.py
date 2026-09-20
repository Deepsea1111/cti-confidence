import pytest

from cti_confidence import AdmiraltyGrade, Credibility, Reliability


def test_parse_round_trips():
    assert AdmiraltyGrade.parse("B2").code == "B2"
    assert AdmiraltyGrade.parse("b2").code == "B2"
    assert AdmiraltyGrade.parse(" a1 ").code == "A1"


@pytest.mark.parametrize("bad", ["", "B", "B22", "Z1", "B7", "12"])
def test_parse_rejects_malformed(bad):
    with pytest.raises(ValueError):
        AdmiraltyGrade.parse(bad)


def test_axes_stay_separate():
    """The scale's whole purpose: a reliable source reporting something improbable."""
    a5 = AdmiraltyGrade.parse("A5")
    assert a5.reliability is Reliability.COMPLETELY_RELIABLE
    assert a5.credibility is Credibility.IMPROBABLE
    # ...and the mirror case, which calls for the opposite follow-up.
    e1 = AdmiraltyGrade.parse("E1")
    assert e1.reliability is Reliability.UNRELIABLE
    assert e1.credibility is Credibility.CONFIRMED


def test_no_single_score_is_exposed():
    """Regression guard for the failure this package exists to prevent.

    If someone later adds a blended numeric score, the two-axis distinction becomes
    lossy the moment anyone uses it. Fail loudly here rather than discovering it in
    a consumer.
    """
    grade = AdmiraltyGrade.parse("B2")
    for attr in ("score", "value", "numeric", "as_float", "weight"):
        assert not hasattr(grade, attr), f"AdmiraltyGrade must not expose {attr!r}"


def test_grades_are_not_ordered():
    """A5 is not 'worse' than D1; ordering them is a category error."""
    with pytest.raises(TypeError):
        _ = AdmiraltyGrade.parse("A5") < AdmiraltyGrade.parse("D1")


def test_cannot_be_judged_is_not_a_bad_grade():
    """F and 6 mean 'no basis to judge' — the absence of a grade, not a low one."""
    f6 = AdmiraltyGrade.parse("F6")
    assert not f6.reliability.is_judgeable
    assert not f6.credibility.is_judgeable
    assert not f6.is_fully_judgeable

    # A single unjudgeable axis is still not fully judgeable.
    assert not AdmiraltyGrade.parse("A6").is_fully_judgeable
    assert not AdmiraltyGrade.parse("F1").is_fully_judgeable
    assert AdmiraltyGrade.parse("A1").is_fully_judgeable


def test_describe_names_both_axes():
    text = AdmiraltyGrade.parse("C3").describe()
    assert "fairly reliable" in text
    assert "possibly true" in text
