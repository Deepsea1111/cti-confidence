import pytest

from cti_confidence import AnalyticConfidence, Likelihood


def test_bands_are_total_and_non_overlapping():
    """Every probability in [0, 1] maps to exactly one band.

    This is the property that makes the scale usable; a gap would let a valid
    probability produce no band, and an overlap would make the mapping depend on
    dict ordering.
    """
    bands = sorted((l.band[0], l.band[1], l) for l in Likelihood)
    assert bands[0][0] == 0.0
    assert bands[-1][1] == 1.0
    for (_, prev_high, _), (next_low, _, _) in zip(bands, bands[1:]):
        assert prev_high == next_low, "bands must be contiguous"


@pytest.mark.parametrize(
    "p,expected",
    [
        (0.0, Likelihood.ALMOST_NO_CHANCE),
        (0.04, Likelihood.ALMOST_NO_CHANCE),
        (0.05, Likelihood.VERY_UNLIKELY),
        (0.30, Likelihood.UNLIKELY),
        (0.50, Likelihood.ROUGHLY_EVEN_CHANCE),
        (0.70, Likelihood.LIKELY),
        (0.90, Likelihood.VERY_LIKELY),
        (0.99, Likelihood.ALMOST_CERTAIN),
        (1.0, Likelihood.ALMOST_CERTAIN),
    ],
)
def test_from_probability(p, expected):
    assert Likelihood.from_probability(p) is expected


def test_boundaries_belong_to_the_upper_band():
    """Half-open [low, high) — a value on the boundary lands in exactly one band."""
    for likelihood in Likelihood:
        low, _ = likelihood.band
        assert Likelihood.from_probability(low) is likelihood


@pytest.mark.parametrize("bad", [-0.01, 1.01, 2.0, -1.0])
def test_out_of_range_raises_rather_than_clamps(bad):
    """Clamping would turn a caller bug into a plausible-looking assessment."""
    with pytest.raises(ValueError):
        Likelihood.from_probability(bad)


def test_likelihood_and_confidence_are_independent():
    """'High confidence that this is very unlikely' must be expressible."""
    assert Likelihood.VERY_UNLIKELY is not AnalyticConfidence.LOW
    assert AnalyticConfidence.HIGH.basis
    assert "independent origin" in AnalyticConfidence.HIGH.basis
