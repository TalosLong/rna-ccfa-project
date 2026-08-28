import unittest

from rna_ccfa.gate_aggregation import (
    AbstainOutcome,
    event_delete_recall,
    event_modification_precision,
    event_preservation,
    precision_improvement_gate,
)


class V201GateAggregationTests(unittest.TestCase):
    def test_abstention_is_original_unchanged(self):
        outcome = AbstainOutcome()
        self.assertEqual(outcome.correct_pair_preservation, 1.0)
        self.assertEqual(outcome.macro_delta_f1, 0.0)
        self.assertIsNone(outcome.modification_precision)

    def test_zero_edit_precision_is_undefined_not_zero(self):
        self.assertIsNone(event_modification_precision(0, 0))
        self.assertEqual(event_modification_precision(8, 2), 0.8)

    def test_event_pooled_recall_and_preservation(self):
        self.assertEqual(event_delete_recall(10, 100), 0.1)
        self.assertEqual(event_preservation(99, 100), 0.99)

    def test_undefined_base_precision_makes_comparison_fail(self):
        self.assertEqual(precision_improvement_gate(0.9, None, 0.02), "FAIL")
        self.assertEqual(precision_improvement_gate(0.9, 0.87, 0.02), "PASS")


if __name__ == "__main__":
    unittest.main()
