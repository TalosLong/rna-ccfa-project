import csv
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "results/selective_refiner/v3_protocol_audit"


class V3ProtocolAuditTests(unittest.TestCase):
    def test_base_support_breakdown_reproduces_authoritative_totals(self):
        with (AUDIT / "base_edit_support_breakdown.csv").open(encoding="utf-8") as handle:
            rows = [row for row in csv.DictReader(handle) if row["source_model"] == "ALL"]
        self.assertEqual(sum(int(row["beneficial_deletions"]) for row in rows), 1571)
        self.assertEqual(sum(int(row["harmful_deletions"]) for row in rows), 282)
        support2 = next(row for row in rows if row["support_other_count"] == "2")
        self.assertEqual(int(support2["beneficial_deletions"]), 18)
        self.assertEqual(int(support2["harmful_deletions"]), 211)

    def test_primary_contract_is_one_hard_veto_without_retraining(self):
        contract = json.loads((AUDIT / "v3_feature_contract.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["primary_cross_model_feature"]["name"], "support_other_count_equals_2")
        self.assertEqual(contract["primary_cross_model_feature"]["type"], "boolean_hard_keep_veto")
        self.assertFalse(contract["new_neural_training_required"])
        self.assertTrue(contract["external77_locked"])

    def test_gate_has_unique_binary_outcomes_and_no_results(self):
        gate = json.loads((AUDIT / "v3_go_no_go.json").read_text(encoding="utf-8"))
        conditions = json.loads((AUDIT / "v3_conditions.json").read_text(encoding="utf-8"))
        self.assertEqual(gate["pass_decision"], "V3_DEVELOPMENT_GATE_PASS")
        self.assertEqual(gate["fail_decision"], "V3_DEVELOPMENT_GATE_FAIL")
        self.assertEqual(gate["undefined_handling"]["required_NA"], "FAIL")
        self.assertFalse(gate["v3_evaluation_executed"])
        self.assertFalse(conditions["v3_development_outcomes_present"])
        self.assertFalse(conditions["external77_evaluated"])


if __name__ == "__main__":
    unittest.main()
