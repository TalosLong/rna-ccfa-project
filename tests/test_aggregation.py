import unittest

from rna_ccfa import aggregate_pair_evaluations, evaluate_pairs


class PairEvaluationAggregationTests(unittest.TestCase):
    @staticmethod
    def _mixed_evaluations():
        return [
            evaluate_pairs([(0, 9), (1, 8)], [(0, 9), (2, 7)], sequence_length=10),
            evaluate_pairs([(0, 9)], [(0, 9)], sequence_length=10),
            evaluate_pairs([], [(1, 8)], sequence_length=10),
        ]

    def test_macro_aggregation_is_arithmetic_mean(self):
        evaluations = self._mixed_evaluations()
        summary = aggregate_pair_evaluations(evaluations)
        self.assertAlmostEqual(
            summary.macro_precision,
            sum(item.precision for item in evaluations) / len(evaluations),
        )
        self.assertAlmostEqual(
            summary.macro_recall,
            sum(item.recall for item in evaluations) / len(evaluations),
        )
        self.assertAlmostEqual(
            summary.macro_f1,
            sum(item.f1 for item in evaluations) / len(evaluations),
        )

    def test_micro_aggregation_sums_counts_before_metrics(self):
        summary = aggregate_pair_evaluations(self._mixed_evaluations())
        self.assertEqual((summary.sum_tp, summary.sum_fp, summary.sum_fn), (2, 1, 2))
        self.assertAlmostEqual(summary.micro_precision, 2 / 3)
        self.assertAlmostEqual(summary.micro_recall, 1 / 2)
        self.assertAlmostEqual(summary.micro_f1, 4 / 7)

    def test_one_perfect_sample(self):
        evaluation = evaluate_pairs([(0, 5)], [(0, 5)], sequence_length=6)
        summary = aggregate_pair_evaluations([evaluation])
        self.assertEqual(summary.n_samples, 1)
        self.assertEqual(summary.macro_f1, 1.0)
        self.assertEqual(summary.micro_f1, 1.0)
        self.assertEqual(summary.median_f1, 1.0)
        self.assertEqual(summary.std_f1, 0.0)

    def test_mixed_tp_fp_fn_samples(self):
        summary = aggregate_pair_evaluations(self._mixed_evaluations())
        self.assertEqual(summary.n_samples, 3)
        self.assertEqual(summary.min_f1, 0.0)
        self.assertEqual(summary.max_f1, 1.0)
        self.assertTrue(0.0 < summary.std_f1 < 1.0)

    def test_aggregation_is_order_independent(self):
        evaluations = self._mixed_evaluations()
        forward = aggregate_pair_evaluations(evaluations)
        reverse = aggregate_pair_evaluations(reversed(evaluations))
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
