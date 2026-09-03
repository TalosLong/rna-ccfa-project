import importlib.util
import math
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
SPEC = importlib.util.spec_from_file_location(
    "summarize_reliability_baseline_r3",
    ROOT / "scripts" / "summarize_reliability_baseline_r3.py",
)
assert SPEC is not None and SPEC.loader is not None
R3 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R3)
bpp_to_delete_risk = R3.bpp_to_delete_risk
brier_score = R3.brier_score
ece_bin_index = R3.ece_bin_index
fixed_bin_ece = R3.fixed_bin_ece
rna_balanced_ece = R3.rna_balanced_ece
average_precision = R3.average_precision
auroc = R3.auroc
utility_metrics = R3.utility_metrics
select_high_preservation_threshold = R3.select_high_preservation_threshold
validate_single_historical_seed = R3.validate_single_historical_seed

RUN_SPEC = importlib.util.spec_from_file_location(
    "run_reliability_baseline_r3",
    ROOT / "scripts" / "run_reliability_baseline_r3.py",
)
assert RUN_SPEC is not None and RUN_SPEC.loader is not None
RUN = importlib.util.module_from_spec(RUN_SPEC)
RUN_SPEC.loader.exec_module(RUN)


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (0.0, 0),
        (0.1, 1),
        (0.9, 9),
        (1.0, 9),
        (math.nextafter(0.1, 0.0), 0),
    ],
)
def test_frozen_ece_boundaries(score, expected):
    assert ece_bin_index(score) == expected


def test_empty_bins_have_zero_contribution_and_na_statistics():
    result = fixed_bin_ece([0.25], [0])
    assert len(result["bins"]) == 10
    empty = result["bins"][0]
    assert empty["count"] == 0
    assert empty["weight"] == 0
    assert empty["mean_score"] is None
    assert empty["observed_delete_rate"] is None
    assert empty["absolute_gap"] is None
    assert empty["ece_contribution"] == 0


def test_perfect_calibration_toy_has_expected_ece():
    result = fixed_bin_ece([0.0, 0.0, 1.0, 1.0], [0, 0, 1, 1])
    assert result["ece"] == pytest.approx(0.0)


def test_miscalibrated_constant_and_p0_reference():
    scores = [0.25] * 4
    labels = [0, 0, 0, 1]
    result = fixed_bin_ece(scores, labels)
    assert result["ece"] == pytest.approx(0.0)
    shifted = fixed_bin_ece([0.5] * 4, labels)
    assert shifted["ece"] == pytest.approx(0.25)
    populated = [row for row in shifted["bins"] if row["count"]]
    assert len(populated) == 1
    assert populated[0]["observed_delete_rate"] == pytest.approx(0.25)


def test_bpp_delete_risk_orientation():
    assert bpp_to_delete_risk(0.8) == pytest.approx(0.2)


def test_brier_is_delete_positive():
    assert brier_score([0.0, 1.0], [0, 1]) == pytest.approx(0.0)
    assert brier_score([1.0, 0.0], [0, 1]) == pytest.approx(1.0)


def test_event_pooled_ece_uses_event_weights():
    result = fixed_bin_ece([0.2, 0.2, 0.8], [0, 0, 1])
    assert result["ece"] == pytest.approx(0.2)
    assert sum(row["weight"] for row in result["bins"]) == pytest.approx(1.0)


def test_rna_balanced_ece_does_not_event_weight_rnas():
    rows = [
        {"rna_id": "many", "score": 0.0, "label_delete": 0},
        {"rna_id": "many", "score": 0.0, "label_delete": 0},
        {"rna_id": "many", "score": 0.0, "label_delete": 0},
        {"rna_id": "one", "score": 0.0, "label_delete": 1},
    ]
    result = rna_balanced_ece(rows)
    assert result["number_of_defined_rnas"] == 2
    assert result["ece"] == pytest.approx(0.5)
    assert fixed_bin_ece(
        [row["score"] for row in rows], [row["label_delete"] for row in rows]
    )["ece"] == pytest.approx(0.25)


@pytest.mark.parametrize("score", [-0.0001, 1.0001, float("nan"), float("inf"), -float("inf")])
def test_invalid_calibration_scores_fail_closed(score):
    with pytest.raises(ValueError):
        fixed_bin_ece([score], [0])


@pytest.mark.parametrize(
    ("scores", "labels", "expected_ap", "expected_roc"),
    [
        ([1.0, 0.0], [1, 0], 1.0, 1.0),
        ([0.0, 1.0], [1, 0], 0.5, 0.0),
        ([0.5, 0.5], [1, 0], 0.5, 0.5),
        ([0.9, 0.8, 0.8, 0.1], [1, 0, 1, 0], 5 / 6, 0.875),
    ],
)
def test_average_precision_and_auroc_toys(scores, labels, expected_ap, expected_roc):
    assert average_precision(scores, labels) == pytest.approx(expected_ap)
    assert auroc(scores, labels) == pytest.approx(expected_roc)


def _utility_rows():
    rows = []
    for rna_id in ("a", "b"):
        for i in range(100):
            rows.append({
                "rna_id": rna_id, "source": "rnafold", "pair_i": i,
                "label_delete": 0, "gt_pair_count": 100,
                "risk": 0.8 if rna_id == "a" and i == 0 else 0.1,
                "partition": "validation",
            })
    rows.extend([
        {"rna_id": "a", "source": "rnafold", "pair_i": 101, "label_delete": 1, "gt_pair_count": 100, "risk": 0.9, "partition": "validation"},
        {"rna_id": "b", "source": "rnafold", "pair_i": 101, "label_delete": 1, "gt_pair_count": 100, "risk": 0.8, "partition": "validation"},
    ])
    return rows


def test_tied_risk_group_deletion_and_risk_utility_accounting():
    rows = _utility_rows()
    flags = [float(row["risk"]) >= 0.8 for row in rows]
    result = utility_metrics(rows, flags)
    event = result["event_pooled"]
    assert event["lost_tp"] == 1
    assert event["removed_fp"] == 2
    assert event["deleted_pair_count"] == 3
    assert event["tp_preservation"] == pytest.approx(199 / 200)
    assert event["fp_removal"] == pytest.approx(1.0)
    assert event["modification_precision"] == pytest.approx(2 / 3)
    assert event["resulting_f1"] is not None


def test_high_preservation_selector_and_tie_breaks():
    threshold, candidates = select_high_preservation_threshold(_utility_rows())
    assert threshold == pytest.approx(0.8)
    selected = next(row for row in candidates if row["selected"])
    assert selected["event_tp_preservation"] >= 0.99
    assert selected["rna_balanced_tp_preservation"] >= 0.99
    # With equal FP removal, higher modification precision and fewer deletions win.
    rows = _utility_rows()
    rows[-1]["risk"] = 0.9
    threshold, _ = select_high_preservation_threshold(rows)
    assert threshold == pytest.approx(0.9)


def test_no_test_thresholding_guard():
    rows = _utility_rows()
    rows[0]["partition"] = "test"
    with pytest.raises(AssertionError, match="validation"):
        select_high_preservation_threshold(rows)


def test_p2_support_orientation():
    pair = (0, 9)
    predictions = {
        "rnafold": {pair}, "petfold": {pair}, "trrosettarna2_native_ss": set()
    }
    assert RUN.support_other_count_risk(pair, "rnafold", predictions) == (1, 1)
    assert RUN.support_other_count_risk(pair, "trrosettarna2_native_ss", predictions) == (2, 0)


def test_p3_fixed_point_semantics():
    assert RUN.v3_fixed_delete(0.9, 0.8, 1) == 1
    assert RUN.v3_fixed_delete(0.9, 0.8, 2) == 0
    assert RUN.v3_fixed_delete(0.9, None, 0) == 0


def test_bpp_parser_squares_root_probability_and_checks_completeness():
    text = "1 2 0.5 ubox\n1 3 0.25 ubox\n2 3 0.0 ubox\n"
    parsed = RUN.parse_bpp_dotplot(text, 3)
    assert parsed == [(0, 1, 0.25), (0, 2, 0.0625), (1, 2, 0.0)]
    with pytest.raises(ValueError, match="incomplete"):
        RUN.parse_bpp_dotplot("1 2 0.5 ubox\n", 3)
    with pytest.raises(ValueError, match="duplicate"):
        RUN.parse_bpp_dotplot(text + "1 2 0.5 ubox\n", 3)


def test_bpp_risk_is_identical_across_all_three_sources():
    joined = {source: bpp_to_delete_risk(0.75) for source in RUN.SOURCES}
    assert joined == {source: 0.25 for source in RUN.SOURCES}


def test_e1_local_conflict_semantics():
    evidence = {(0, 9)}
    assert RUN.local_evidence_conflict_risk((0, 9), RUN.PAIR_CHANNEL, evidence, set()) == 0
    assert RUN.local_evidence_conflict_risk((0, 8), RUN.PAIR_CHANNEL, evidence, set()) == 1
    assert RUN.local_evidence_conflict_risk((1, 8), RUN.PAIR_CHANNEL, evidence, set()) == 0
    assert RUN.local_evidence_conflict_risk((2, 7), RUN.UNPAIRED_CHANNEL, set(), {2}) == 1


def test_e2_disagreement_semantics():
    assert RUN.b2_disagreement_risk((0, 9), {(0, 9)}) == 0
    assert RUN.b2_disagreement_risk((0, 9), {(1, 8)}) == 1


def test_r2_eligible_manifest_guard():
    rows = (
        [{"channel": RUN.PAIR_CHANNEL, "eligibility_status": "R2_ELIGIBLE"}] * 3523
        + [{"channel": RUN.UNPAIRED_CHANNEL, "eligibility_status": "R2_ELIGIBLE"}] * 3630
        + [{"channel": RUN.PAIR_CHANNEL, "eligibility_status": "R2_INELIGIBLE"}] * 107
    )
    counts = RUN.validate_r2_eligibility_counts(rows)
    assert counts[RUN.PAIR_CHANNEL] == 3523
    with pytest.raises(AssertionError):
        RUN.validate_r2_eligibility_counts(rows[:-108])


def test_rna_balanced_utility_does_not_event_weight_rnas():
    rows = [
        {"rna_id": "many", "source": "rnafold", "label_delete": 1, "gt_pair_count": 0, "risk": 1},
        {"rna_id": "many", "source": "rnafold", "label_delete": 1, "gt_pair_count": 0, "risk": 1},
        {"rna_id": "many", "source": "rnafold", "label_delete": 1, "gt_pair_count": 0, "risk": 1},
        {"rna_id": "one", "source": "rnafold", "label_delete": 1, "gt_pair_count": 0, "risk": 0},
    ]
    result = utility_metrics(rows, [True, True, True, False])
    assert result["event_pooled"]["fp_removal"] == pytest.approx(0.75)
    assert result["rna_balanced"]["fp_removal"] == pytest.approx(0.5)


def test_seed_handling_guard_rejects_pooled_model_seeds():
    validate_single_historical_seed([{"historical_seed": 17}], 17)
    with pytest.raises(AssertionError, match="separate"):
        validate_single_historical_seed([{"historical_seed": 17}, {"historical_seed": 29}], 17)
