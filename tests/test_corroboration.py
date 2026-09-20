from cti_confidence import AdmiraltyGrade, Report, corroborate

A1 = AdmiraltyGrade.parse("A1")
B2 = AdmiraltyGrade.parse("B2")
F6 = AdmiraltyGrade.parse("F6")


def r(source, origin, grade=B2):
    return Report(source_id=source, origin_id=origin, grade=grade)


def test_circular_reporting_collapses_to_one_origin():
    """The failure this module exists for: one claim, five republications."""
    reports = [
        r("origin-blog", "origin-blog"),
        r("aggregator-a", "origin-blog"),
        r("aggregator-b", "origin-blog"),
        r("newsletter-c", "origin-blog"),
        r("vendor-feed-d", "origin-blog"),
    ]
    result = corroborate(reports)
    assert result.report_count == 5
    assert result.independent_origins == 1, "five copies are not five sources"
    assert result.circular_reports == 4
    assert result.inflation_factor == 5.0


def test_genuinely_independent_origins_count():
    result = corroborate([
        r("vendor-a", "vendor-a"),
        r("cert-b", "cert-b"),
        r("own-telemetry", "own-telemetry"),
    ])
    assert result.independent_origins == 3
    assert result.circular_reports == 0
    assert result.inflation_factor == 1.0


def test_mixed_case_counts_origins_not_reports():
    result = corroborate([
        r("vendor-a", "vendor-a"),
        r("aggregator", "vendor-a"),
        r("cert-b", "cert-b"),
    ])
    assert result.independent_origins == 2
    assert result.circular_reports == 1
    assert result.origins == ("vendor-a", "cert-b")


def test_ungradeable_origins_reported_separately():
    """'Three origins, two ungradeable' must not flatten to 'three origins'."""
    result = corroborate([
        r("a", "a", A1),
        r("b", "b", F6),
        r("c", "c", F6),
    ])
    assert result.independent_origins == 3
    assert set(result.unjudgeable_origins) == {"b", "c"}
    assert "ungradeable" in result.summary()


def test_one_gradeable_report_rescues_its_origin():
    """An origin is ungradeable only if *every* report of it was ungradeable."""
    result = corroborate([r("a", "a", F6), r("a-again", "a", A1)])
    assert result.unjudgeable_origins == ()


def test_empty_input_is_zero_not_one():
    result = corroborate([])
    assert result.independent_origins == 0
    assert result.report_count == 0
    assert result.inflation_factor == 0.0


def test_corroborate_returns_no_confidence_value():
    """How many origins justify what confidence is an analytic judgement.

    Guard against a future convenience property that would invent precision.
    """
    result = corroborate([r("a", "a")])
    for attr in ("confidence", "score", "level", "rating"):
        assert not hasattr(result, attr), f"Corroboration must not expose {attr!r}"


def test_is_original_flags_the_origin_itself():
    assert r("a", "a").is_original
    assert not r("aggregator", "a").is_original
