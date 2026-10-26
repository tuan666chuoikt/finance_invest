"""Hand-computed cases for R7/R8 (G10, G8 self-consistency, summary, ref_check)."""

from datetime import date
from decimal import Decimal

from finvest_analytics.adjust.recon import (
    SELF_CONSISTENCY,
    UNIT_OR_ADAPTER,
    ReconResult,
    reconcile,
    ref_check,
    summary,
)
from finvest_analytics.domain.models import AdjBar, Factor, NominalBar

D = date.fromisoformat


def nom(d, c, kind="observed"):
    return NominalBar("FPT", D(d), c, kind)


def src(d, c):
    return AdjBar("FPT", D(d), Decimal(c))


def test_g10_one_row_and_pct_rounding():
    fs = [Factor("FPT", D("2026-10-05"), Decimal("0.98"))]
    r = reconcile(
        [nom("2026-10-01", 50000), nom("2026-10-02", 50000), nom("2026-10-06", 93500)],
        fs,
        [src("2026-10-01", "48900"), src("2026-10-02", "48980"), src("2026-10-06", "93500")],
    )
    # ours 49,000: |100|/48,900 = 0.2045 % (row); |20|/48,980 = 0.0408 % (none); G = 1 and equal -> 0
    assert [(m.trading_date, m.ours, m.theirs, m.diff_pct) for m in r.mismatches] == [
        (D("2026-10-01"), 49000, 48900, Decimal("0.2045"))
    ]
    assert (r.checked, r.exact_days, r.first_mismatch) == (3, 1, D("2026-10-01"))


def test_g_equals_one_one_vnd_diff_is_flagged_though_under_threshold():
    r = reconcile([nom("2026-10-06", 93500)], [], [src("2026-10-06", "93501")])
    (m,) = r.mismatches  # 1/93,501 = 0.0011 % < 0.1 % but G = 1 demands equality
    assert (m.note, m.diff_pct) == (UNIT_OR_ADAPTER, Decimal("0.0011"))


def test_thousand_vnd_adapter_diff_pct_is_capped_to_fit_numeric_8_4():
    r = reconcile([nom("2026-10-06", 93500)], [], [src("2026-10-06", "93.5")])
    (m,) = r.mismatches  # uncapped 99900.0000 would overflow recon_mismatches.diff_pct
    assert (m.note, m.diff_pct) == (UNIT_OR_ADAPTER, Decimal("9999.9999"))


def test_ex_date_after_last_source_bar_is_not_applied():
    fs = [Factor("FPT", D("2026-11-02"), Decimal("0.5"))]
    assert not reconcile([nom("2026-10-06", 93500)], fs, [src("2026-10-06", "93500")]).mismatches


def test_g8_self_consistency_passes_and_hand_broken_a_fails():
    fs = [
        Factor("FPT", D("2026-10-05"), Decimal("0.98")),
        Factor("FPT", D("2026-10-07"), Decimal("0.769230769231")),
    ]
    last = src("2026-10-09", "70000")
    ok = reconcile([nom("2026-10-02", 51000, "reconstructed")], fs, [src("2026-10-02", "38446"), last])
    # G = 0.753846153846; 51,000 x G = 38,446.15 vs 38,446.00 -> 0.15 VND <= 1
    assert (ok.checked, ok.mismatches) == (1, [])
    bad = reconcile([nom("2026-10-02", 51000, "reconstructed")], fs, [src("2026-10-02", "38448"), last])
    # 1.85 VND off = 0.005 %: under the 0.1 % threshold, still over 1 VND
    assert [m.note for m in bad.mismatches] == [SELF_CONSISTENCY]


def test_summary_missing_symbol_is_listed_and_not_a_pass():
    expected = {f"S{i:02d}" for i in range(30)}  # S29 gets the mismatch below
    ok = ReconResult([], 5, 5, None)
    res = {s: ok for s in sorted(expected)[:29]}
    assert summary(res, expected) == "29/30, 0 mismatches; missing S29"
    res["S29"] = ReconResult([], 0, 0, None)  # nothing compared is still missing
    assert summary(res, expected).startswith("29/30")
    m = reconcile([nom("2026-09-18", 100)], [], [src("2026-09-18", "101")]).mismatches
    res["S29"] = ReconResult(m, 1, 0, D("2026-09-18"))
    assert summary(res, expected) == "30/30, 1 mismatches; first mismatch S29 2026-09-18"


def test_ref_check_within_one_tick():
    f = Decimal("0.98")  # 0.98 x 50,000 = 49,000, tick 50
    assert ref_check(f, 50000, 49000, 50) and ref_check(f, 50000, 49050, 50)
    assert not ref_check(f, 50000, 49100, 50)
    g = Decimal("0.769230769231")  # x 93,500 = 71,923.08 -> 71,900 at tick 100
    assert ref_check(g, 93500, 71900, 100) and not ref_check(g, 93500, 72100, 100)


def test_g13_recon_uses_each_rows_own_version_last():
    fs = [Factor("FPT", D("2026-10-11"), Decimal("0.98"))]
    nominal = [nom("2026-10-05", 50000, "reconstructed"), nom("2026-10-09", 50000, "reconstructed")]
    v0 = AdjBar(
        "FPT", D("2026-10-05"), Decimal("50000"), D("2026-10-10")
    )  # fetched before the ex-date: G_v = 1
    v1 = AdjBar("FPT", D("2026-10-09"), Decimal("49000"), D("2026-10-12"))  # after it: G_v = 0.98
    r = reconcile(nominal, fs, [v0, v1])
    assert (r.checked, r.exact_days, r.mismatches) == (2, 2, [])
    # without `last` the list's max date (10-12) applies to the V0 row too: ours 49,000 vs 50,000
    legacy = [
        AdjBar("FPT", D("2026-10-05"), Decimal("50000")),
        AdjBar("FPT", D("2026-10-09"), Decimal("49000")),
        AdjBar("FPT", D("2026-10-12"), Decimal("49000")),
    ]
    assert reconcile(nominal, fs, legacy).exact_days == 1


def test_self_check_false_judges_reconstructed_rows_like_observed():
    fs = [Factor("FPT", D("2026-10-05"), Decimal("0.909090909091"))]
    last = src("2026-10-09", "70000")
    rows, theirs = [nom("2026-10-02", 71701, "reconstructed")], [src("2026-10-02", "65180.00"), last]
    # ours 71,701 x 0.909090909091 = 65,182.73 vs 65,180.00: 2.73 > 1 VND but 0.0042 % < 0.1 %
    assert [m.note for m in reconcile(rows, fs, theirs).mismatches] == [SELF_CONSISTENCY]
    r = reconcile(rows, fs, theirs, self_check=False)
    assert (r.mismatches, r.checked) == ([], 1)
    exact = reconcile([nom("2026-10-06", 71701, "reconstructed")], [], [src("2026-10-06", "71700")], self_check=False)
    assert [m.note for m in exact.mismatches] == [UNIT_OR_ADAPTER]
