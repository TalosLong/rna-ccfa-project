"""Frozen Conservative Evidence Reconciliation (CER/CCEG) primitives.

This module implements the prospectively frozen CER development contract.  It
does not discover data paths, choose a model variant, or access an independent
dataset.  Callers must pass explicitly allowlisted Legacy121 development
artifacts through :func:`guard_cer_path`.
"""
from __future__ import annotations

from collections import defaultdict
import math
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np

from .evidence_reconciliation import (
    ITEM_DIM,
    TRAINING_CONFIG,
    apply_platt,
    fit_monotone_platt,
    make_ern_model,
    mean_defined,
    population_summary,
    safe_ratio,
    utility_metrics,
)


CER_PROTOCOL_SHA256 = "b2ed83b7e1b9bcf992a3f8e562b640968692693cbdee4aa3d94ac3b7da54179a"
CER_IMPLEMENTATION_PLAN_SHA256 = "d496fea068032ef6b5e823d6c8b9b97d26e9db7a54ca217256446cfe96034119"
R4_PROTOCOL_SHA256 = "81ce3923c19a99094418dc5fb568c7081192ac84c542b33dbb4bafa888c739e4"
R4_RESULTS_SHA256 = "728e931d4e1329935fe990154940cb0b35900f56d14298d88ef59a7ad8e3fc8c"
R4_POSTMORTEM_SHA256 = "a7645521b6721eee159c5f009088c742ab5ad053b6bd1a63c9a92b485ab18218"
R4_FEATURE_CONTRACT_SHA256 = "154d9e2a59c2d571369edc516c0932b41adb8bea62943a3de6920431e9c7ad28"
R4_GAIN_SUMMARY_SHA256 = "467c4d17adf610edb7c4dc3b3e596ec3793376d885fb01af434c92122e485935"
FROZEN_SPLIT_SHA256 = "810b04a3963acc7637b60fcb5c2246c765fac334f809a5af9f8f050824ed974f"
FROZEN_CLEAN_MANIFEST_SHA256 = "c743913d8d0b44cbccaba74b68bebaeb1551a4095d1ae51782435c12e96d11ca"

CONDITIONS = ("CER", "CER_EVIDENCE_MASKED")
BRANCHES = ("EVIDENCE_BRANCH", "CONTEXT_BRANCH")
CHANNELS = ("positive_pair", "unpaired")
ROTATIONS = (0, 1, 2, 3, 4)
MODEL_SEEDS = (17, 29, 41, 53, 67)
SOURCES = ("rnafold", "petfold", "trrosettarna2_native_ss")
SCOPES = ("DIRECT", "LOCAL_CONFLICT", "NON_EVIDENCED")
ACTIONS = ("KEEP", "DELETE", "ABSTAIN")

R4_GAIN_EVENT = 0.08890968834013739
R4_GAIN_RNA = 0.045569629647920704
R4_NON_EVIDENCED_LOST_TP = 2687.8


def guard_cer_path(path: Path) -> Path:
    """Reject every scientifically forbidden path before opening it."""
    lowered = str(path).lower()
    forbidden = (
        "external77", "noisy_evidence", "controlled_noise", "real_evidence",
        "shape", "dms", "pars",
    )
    if any(token in lowered for token in forbidden):
        raise PermissionError(f"CER forbidden path: {path}")
    historical = (
        "run_evidence_guidance_stage_e2", "evidence_refiner.py",
        "results/evidence_guidance/stage_e2/",
    )
    if any(token in lowered for token in historical):
        raise PermissionError(f"historical E2 execution path forbidden: {path}")
    return path


def development_split_roles(
    fold_by_rna: Mapping[str, int], rotation: int
) -> dict[str, set[str]]:
    """Return the frozen development roles; no test-role alias is exposed."""
    rotation = int(rotation)
    if rotation not in ROTATIONS:
        raise ValueError(rotation)
    validation = (rotation + 1) % 5
    roles = {
        "development_train": {
            rna for rna, fold in fold_by_rna.items()
            if int(fold) not in (rotation, validation)
        },
        "development_validation": {
            rna for rna, fold in fold_by_rna.items() if int(fold) == validation
        },
        "development_assessment": {
            rna for rna, fold in fold_by_rna.items() if int(fold) == rotation
        },
    }
    values = list(roles.values())
    if any(values[i] & values[j] for i in range(3) for j in range(i + 1, 3)):
        raise AssertionError("RNA development-role leakage")
    if set().union(*values) != set(fold_by_rna):
        raise AssertionError("RNA development roles are incomplete")
    return roles


def complete_run_keys() -> list[tuple[str, str, str, int, int]]:
    return [
        (condition, branch, channel, rotation, seed)
        for condition in CONDITIONS
        for branch in BRANCHES
        for channel in CHANNELS
        for rotation in ROTATIONS
        for seed in MODEL_SEEDS
    ]


def branch_uses_evidence(condition: str, branch: str) -> bool:
    if condition not in CONDITIONS or branch not in BRANCHES:
        raise ValueError((condition, branch))
    return condition == "CER" and branch == "EVIDENCE_BRANCH"


def operational_scope(condition: str, evaluation_scope: str) -> str:
    if condition not in CONDITIONS or evaluation_scope not in SCOPES:
        raise ValueError((condition, evaluation_scope))
    return evaluation_scope if condition == "CER" else "NON_EVIDENCED"


def make_cer_branch_model(channel: str):
    if channel not in CHANNELS:
        raise ValueError(channel)
    return make_ern_model(ITEM_DIM[channel])


def logit_clip(probabilities: Sequence[float], epsilon: float = 1e-7) -> np.ndarray:
    values = np.clip(np.asarray(probabilities, dtype=np.float64), epsilon, 1.0 - epsilon)
    if values.ndim != 1 or not np.isfinite(values).all():
        raise ValueError("probabilities must be a finite one-dimensional array")
    return np.log(values / (1.0 - values))


def fit_policy_platt(raw_scores: Sequence[float], labels: Sequence[int]) -> dict[str, object]:
    transformed = logit_clip(raw_scores)
    result = fit_monotone_platt(transformed, labels)
    if float(result["a"]) <= 0.0:
        raise RuntimeError("CCEG policy calibration requires a_G > 0")
    result.update({
        "a_G": result.pop("a"),
        "b_G": result.pop("b"),
        "a_constraint": "a_G > 0",
        "input_transform": "logit(clip(r_CCEG,1e-7,1-1e-7))",
    })
    return result


def apply_policy_platt(
    raw_scores: Sequence[float], calibration: Mapping[str, object]
) -> np.ndarray:
    a = float(calibration["a_G"])
    if a <= 0:
        raise ValueError("CCEG policy slope must be strictly positive")
    return apply_platt(logit_clip(raw_scores), a, float(calibration["b_G"]))


def inverse_policy_cutoff(
    threshold: float | None, calibration: Mapping[str, object]
) -> float | None:
    if threshold is None:
        return None
    tau = float(threshold)
    if not 0.0 < tau < 1.0:
        raise ValueError("numeric CCEG threshold must lie strictly inside (0,1)")
    a = float(calibration["a_G"])
    b = float(calibration["b_G"])
    if a <= 0 or not math.isfinite(b):
        raise ValueError("invalid CCEG policy calibrator")
    transformed = (math.log(tau / (1.0 - tau)) - b) / a
    if transformed >= 0:
        return 1.0 / (1.0 + math.exp(-transformed))
    exponent = math.exp(transformed)
    return exponent / (1.0 + exponent)


def corroborated_scores(q_e: Sequence[float], q_c: Sequence[float]) -> np.ndarray:
    evidence = np.asarray(q_e, dtype=np.float64)
    context = np.asarray(q_c, dtype=np.float64)
    if evidence.shape != context.shape or evidence.ndim != 1:
        raise ValueError("q_E and q_C must be equal one-dimensional arrays")
    if not np.isfinite(evidence).all() or not np.isfinite(context).all():
        raise ValueError("branch probabilities must be finite")
    if ((evidence < 0) | (evidence > 1) | (context < 0) | (context > 1)).any():
        raise ValueError("branch probabilities must lie in [0,1]")
    return np.minimum(evidence, context)


def cceg_actions(
    q_e: Sequence[float],
    q_c: Sequence[float],
    scopes: Sequence[str],
    raw_cutoff: float | None,
    *,
    artifacts_valid: bool = True,
) -> list[str]:
    evidence = np.asarray(q_e, dtype=np.float64)
    context = np.asarray(q_c, dtype=np.float64)
    if evidence.shape != context.shape or len(evidence) != len(scopes):
        raise ValueError("CCEG action inputs differ in length")
    if not artifacts_valid:
        return ["ABSTAIN"] * len(scopes)
    if raw_cutoff is not None and not 0.0 <= float(raw_cutoff) <= 1.0:
        raise ValueError("invalid raw corroboration cutoff")
    actions: list[str] = []
    for qe, qc, scope in zip(evidence, context, scopes):
        if scope not in SCOPES:
            actions.append("ABSTAIN")
        elif scope == "DIRECT":
            actions.append("KEEP")
        elif scope == "LOCAL_CONFLICT":
            actions.append("DELETE")
        elif raw_cutoff is None:
            actions.append("KEEP")
        elif qe >= raw_cutoff and qc >= raw_cutoff:
            actions.append("DELETE")
        elif qe < raw_cutoff and qc < raw_cutoff:
            actions.append("KEEP")
        else:
            actions.append("ABSTAIN")
    return actions


def _policy_curve(
    rows: Sequence[Mapping[str, object]], scores: np.ndarray
) -> list[dict[str, object]]:
    labels = np.asarray([int(row["label_delete"]) for row in rows], dtype=np.int8)
    scopes = np.asarray([str(row["operational_scope"]) for row in rows], dtype=object)
    rna_names = sorted({str(row["rna_id"]) for row in rows})
    rna_lookup = {rna: i for i, rna in enumerate(rna_names)}
    rna_ids = np.asarray([rna_lookup[str(row["rna_id"])] for row in rows], dtype=np.int32)
    tp_total = int((labels == 0).sum())
    fp_total = int((labels == 1).sum())
    tp_by_rna = np.bincount(rna_ids[labels == 0], minlength=len(rna_names)).astype(np.int64)
    fp_by_rna = np.bincount(rna_ids[labels == 1], minlength=len(rna_names)).astype(np.int64)

    fixed = scopes == "LOCAL_CONFLICT"
    if ((scopes == "DIRECT") & fixed).any():
        raise AssertionError("scope precedence is not unique")
    fixed_labels = labels[fixed]
    lost = int((fixed_labels == 0).sum())
    removed = int((fixed_labels == 1).sum())
    lost_by_rna = np.bincount(rna_ids[fixed & (labels == 0)], minlength=len(rna_names)).astype(np.int64)
    removed_by_rna = np.bincount(rna_ids[fixed & (labels == 1)], minlength=len(rna_names)).astype(np.int64)
    candidates: list[dict[str, object]] = []

    def append(tau: float | None) -> None:
        deleted_by_rna = lost_by_rna + removed_by_rna
        tp_values = 1.0 - np.divide(
            lost_by_rna, tp_by_rna, out=np.zeros(len(rna_names)), where=tp_by_rna > 0
        )
        fp_values = np.divide(
            removed_by_rna, fp_by_rna, out=np.zeros(len(rna_names)), where=fp_by_rna > 0
        )
        mp_values = np.divide(
            removed_by_rna, deleted_by_rna, out=np.zeros(len(rna_names)), where=deleted_by_rna > 0
        )
        event_tp = 1.0 - lost / tp_total
        rna_tp = float(tp_values[tp_by_rna > 0].mean())
        candidates.append({
            "threshold": tau,
            "threshold_semantics": "DELETE_NO_NON_EVIDENCED" if tau is None else "DELETE_Q_CCEG_GTE",
            "eligible": event_tp >= 0.99 and rna_tp >= 0.99,
            "event_tp_preservation": event_tp,
            "event_fp_removal": removed / fp_total,
            "event_modification_precision": safe_ratio(removed, lost + removed),
            "event_deleted_pair_count": lost + removed,
            "rna_balanced_tp_preservation": rna_tp,
            "rna_balanced_fp_removal": float(fp_values[fp_by_rna > 0].mean()),
            "rna_balanced_modification_precision": (
                float(mp_values[deleted_by_rna > 0].mean())
                if (deleted_by_rna > 0).any() else None
            ),
        })

    append(None)
    eligible_indices = np.flatnonzero(scopes == "NON_EVIDENCED")
    order = eligible_indices[np.argsort(-scores[eligible_indices], kind="stable")]
    start = 0
    while start < len(order):
        score = scores[order[start]]
        end = start + 1
        while end < len(order) and scores[order[end]] == score:
            end += 1
        block = order[start:end]
        block_labels = labels[block]
        lost += int((block_labels == 0).sum())
        removed += int((block_labels == 1).sum())
        np.add.at(lost_by_rna, rna_ids[block[block_labels == 0]], 1)
        np.add.at(removed_by_rna, rna_ids[block[block_labels == 1]], 1)
        append(float(score))
        start = end
    return candidates


def conservative_threshold_search(
    rows: Sequence[Mapping[str, object]],
) -> tuple[float | None, list[dict[str, object]]]:
    """Validation-only CCEG threshold selection with indivisible score ties."""
    if not rows or any(str(row["partition"]) != "development_validation" for row in rows):
        raise AssertionError("CER threshold selection accepts development_validation only")
    scores = np.asarray([float(row["q_cceg"]) for row in rows], dtype=np.float64)
    if not np.isfinite(scores).all() or ((scores < 0) | (scores > 1)).any():
        raise ValueError("invalid calibrated CCEG score")
    curve = _policy_curve(rows, scores)
    eligible = [point for point in curve if point["eligible"]]
    if not eligible:
        raise AssertionError("fixed local policy must have an eligible no-propagation point")

    def key(point: Mapping[str, object]) -> tuple[float, float, int, float]:
        mp = point["rna_balanced_modification_precision"]
        tau = math.inf if point["threshold"] is None else float(point["threshold"])
        return (
            float(point["rna_balanced_fp_removal"]),
            -math.inf if mp is None else float(mp),
            -int(point["event_deleted_pair_count"]),
            tau,
        )

    selected = max(eligible, key=key)
    for point in curve:
        point["selected"] = point is selected
    return selected["threshold"], curve


def action_accounting(
    rows: Sequence[Mapping[str, object]], actions: Sequence[str]
) -> dict[str, object]:
    if len(rows) != len(actions) or any(action not in ACTIONS for action in actions):
        raise ValueError("invalid action accounting inputs")
    delete = np.asarray([action == "DELETE" for action in actions], dtype=bool)
    utility = utility_metrics(rows, delete)
    counts = {action: sum(value == action for value in actions) for action in ACTIONS}
    counts["total"] = len(actions)
    counts["outside_explicit_delete_count"] = sum(
        action == "DELETE" and str(row["evaluation_scope"]) == "NON_EVIDENCED"
        for row, action in zip(rows, actions)
    )
    counts["outside_explicit_delete_fraction"] = safe_ratio(
        counts["outside_explicit_delete_count"], counts["DELETE"]
    )
    return {"utility": utility, "actions": counts}


def scope_accounting(
    rows: Sequence[Mapping[str, object]], actions: Sequence[str]
) -> dict[str, object]:
    output: dict[str, object] = {}
    for scope in SCOPES:
        indices = [i for i, row in enumerate(rows) if str(row["evaluation_scope"]) == scope]
        selected_rows = [rows[i] for i in indices]
        selected_actions = [actions[i] for i in indices]
        labels = np.asarray([int(row["label_delete"]) for row in selected_rows], dtype=np.int8)
        delete = np.asarray([action == "DELETE" for action in selected_actions], dtype=bool)
        per_rna_counts: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0, 0])
        for row, label, deleted in zip(selected_rows, labels, delete):
            values = per_rna_counts[str(row["rna_id"])]
            values[0] += 1
            values[1] += int(label == 0)
            values[2] += int(label == 1)
            values[3] += int(label == 0 and deleted)
            values[4] += int(label == 1 and deleted)
        rna_ids = sorted(per_rna_counts)
        per_rna = []
        for rna in rna_ids:
            count, tp, fp, lost, removed = per_rna_counts[rna]
            per_rna.append({
                "tp_preservation": None if not tp else 1.0 - lost / tp,
                "fp_removal": None if not fp else removed / fp,
                "modification_precision": safe_ratio(removed, lost + removed),
                "coverage": safe_ratio(lost + removed, count),
            })
        tp = int((labels == 0).sum()); fp = int((labels == 1).sum())
        lost = int(((labels == 0) & delete).sum()); removed = int(((labels == 1) & delete).sum())
        event = {
            "opportunity_count": len(indices), "tp_opportunity_count": tp,
            "fp_opportunity_count": fp, "deleted_pair_count": int(delete.sum()),
            "removed_fp": removed, "lost_tp": lost,
            "tp_preservation": None if not tp else 1.0 - lost / tp,
            "fp_removal": None if not fp else removed / fp,
            "modification_precision": safe_ratio(removed, lost + removed),
            "coverage": safe_ratio(int(delete.sum()), len(indices)),
            **{f"action_{action.lower()}": selected_actions.count(action) for action in ACTIONS},
        }
        balanced: dict[str, object] = {"rna_count": len(rna_ids)}
        for metric in ("tp_preservation", "fp_removal", "modification_precision", "coverage"):
            balanced[metric], balanced[f"{metric}_defined_rnas"] = mean_defined(
                item[metric] for item in per_rna
            )
        balanced.update({"lost_tp": lost, "removed_fp": removed})
        output[scope] = {"event_pooled": event, "rna_balanced": balanced}
    if sum(output[scope]["event_pooled"]["opportunity_count"] for scope in SCOPES) != len(rows):
        raise AssertionError("evaluation scope partition is not exhaustive")
    return output


def evaluate_conservative_dev_gate(
    primary: Mapping[str, float],
    non_evidenced: Mapping[str, float],
    masked_non_evidenced: Mapping[str, float],
    cer_source_rna_fp: Mapping[str, float],
    masked_source_rna_fp: Mapping[str, float],
    p3_source_rna_fp: Mapping[str, float],
    *,
    complete_and_valid: bool,
) -> dict[str, object]:
    overall = {
        "event_tp_preservation_gte_0_99": float(primary["event_tp_preservation"]) >= 0.99,
        "rna_tp_preservation_gte_0_99": float(primary["rna_tp_preservation"]) >= 0.99,
        "event_fp_removal_gt_0_347816": float(primary["event_fp_removal"]) > 0.347816,
        "rna_fp_removal_gt_0_489748": float(primary["rna_fp_removal"]) > 0.489748,
    }
    p3_improvement = {
        source: float(cer_source_rna_fp[source]) - float(p3_source_rna_fp[source])
        for source in SOURCES
    }
    p3_positive = [source for source, value in p3_improvement.items() if value > 0]
    source_condition = len(p3_positive) >= 2 and any(
        source in p3_positive for source in ("rnafold", "petfold")
    )
    safety = {
        "event_non_evidenced_tp_preservation_gte_0_99": float(non_evidenced["event_tp_preservation"]) >= 0.99,
        "rna_non_evidenced_tp_preservation_gte_0_99": float(non_evidenced["rna_tp_preservation"]) >= 0.99,
        "event_non_evidenced_preservation_gte_masked": float(non_evidenced["event_tp_preservation"]) >= float(masked_non_evidenced["event_tp_preservation"]),
        "rna_non_evidenced_preservation_gte_masked": float(non_evidenced["rna_tp_preservation"]) >= float(masked_non_evidenced["rna_tp_preservation"]),
        "mean_non_evidenced_lost_tp_lt_2687_8": float(non_evidenced["lost_tp"]) < R4_NON_EVIDENCED_LOST_TP,
    }
    g_event = float(primary["event_fp_removal"]) - float(primary["masked_event_fp_removal"])
    g_rna = float(primary["rna_fp_removal"]) - float(primary["masked_rna_fp_removal"])
    source_gains = {
        source: float(cer_source_rna_fp[source]) - float(masked_source_rna_fp[source])
        for source in SOURCES
    }
    evidence_positive_sources = [source for source, value in source_gains.items() if value > 0]
    evidence_source_condition = len(evidence_positive_sources) >= 2 and any(
        source in evidence_positive_sources for source in ("rnafold", "petfold")
    )
    evidence = {
        "g_event_gt_0": g_event > 0,
        "g_rna_gt_0": g_rna > 0,
        "source_wise_positive_2_of_3_including_rnafold_or_petfold": evidence_source_condition,
        "event_r4_gain_retention_gt_0_50": g_event / R4_GAIN_EVENT > 0.50,
        "rna_r4_gain_retention_gt_0_50": g_rna / R4_GAIN_RNA > 0.50,
    }
    passed = complete_and_valid and all(overall.values()) and source_condition and all(safety.values()) and all(evidence.values())
    return {
        "status": "CONSERVATIVE_DEV_GATE_PASS_DEVELOPMENT_ONLY" if passed else "CONSERVATIVE_DEV_GATE_FAIL",
        "legacy121_role": "DEVELOPMENT_ONLY", "independent_confirmation": False,
        "complete_and_valid": bool(complete_and_valid), "overall_criteria": overall,
        "p3_source_improvement": p3_improvement, "p3_positive_sources": p3_positive,
        "p3_source_condition": source_condition, "non_evidenced_safety": safety,
        "g_event": g_event, "g_rna": g_rna,
        "event_r4_gain_retention_ratio": g_event / R4_GAIN_EVENT,
        "rna_r4_gain_retention_ratio": g_rna / R4_GAIN_RNA,
        "evidence_source_gains": source_gains,
        "evidence_positive_sources": evidence_positive_sources,
        "evidence_attribution_criteria": evidence,
        "all_criteria_conjunctive": True, "rescue_tuning_performed": False,
        "r4_gate_b_decision": "R4_GATE_B_FAIL",
    }


__all__ = [
    "ACTIONS", "BRANCHES", "CER_IMPLEMENTATION_PLAN_SHA256", "CER_PROTOCOL_SHA256",
    "CHANNELS", "CONDITIONS", "FROZEN_CLEAN_MANIFEST_SHA256", "FROZEN_SPLIT_SHA256",
    "MODEL_SEEDS", "ROTATIONS", "SCOPES", "SOURCES", "TRAINING_CONFIG",
    "action_accounting", "apply_policy_platt", "branch_uses_evidence",
    "cceg_actions", "complete_run_keys", "conservative_threshold_search",
    "corroborated_scores", "development_split_roles", "evaluate_conservative_dev_gate",
    "fit_policy_platt", "guard_cer_path", "inverse_policy_cutoff", "make_cer_branch_model",
    "operational_scope", "population_summary", "scope_accounting",
]
