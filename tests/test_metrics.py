import unittest

from rna_ccfa import StructureValidationError, evaluate_pairs


class PairMetricTests(unittest.TestCase):
    def test_perfect_prediction(self):
        result = evaluate_pairs(
            [(0, 9), (1, 8), (2, 7)],
            [(0, 9), (1, 8), (2, 7)],
            sequence_length=10,
        )
        self.assertEqual((result.tp, result.fp, result.fn), (3, 0, 0))
        self.assertEqual((result.precision, result.recall, result.f1), (1.0, 1.0, 1.0))

    def test_partial_prediction(self):
        result = evaluate_pairs(
            [(0, 9), (2, 7)],
            [(0, 9), (1, 8), (2, 7)],
            sequence_length=10,
        )
        self.assertEqual((result.tp, result.fp, result.fn), (2, 0, 1))
        self.assertEqual(result.true_positive_pairs, ((0, 9), (2, 7)))
        self.assertEqual(result.false_negative_pairs, ((1, 8),))
        self.assertEqual(result.precision, 1.0)
        self.assertAlmostEqual(result.recall, 2 / 3)
        self.assertAlmostEqual(result.f1, 0.8)

    def test_false_positives(self):
        result = evaluate_pairs(
            [(0, 9), (1, 8)],
            [(0, 9)],
            sequence_length=10,
        )
        self.assertEqual((result.tp, result.fp, result.fn), (1, 1, 0))
        self.assertEqual(result.false_positive_pairs, ((1, 8),))
        self.assertEqual(result.precision, 0.5)
        self.assertEqual(result.recall, 1.0)
        self.assertAlmostEqual(result.f1, 2 / 3)

    def test_false_negatives(self):
        result = evaluate_pairs(
            [(0, 9)],
            [(0, 9), (1, 8)],
            sequence_length=10,
        )
        self.assertEqual((result.tp, result.fp, result.fn), (1, 0, 1))
        self.assertEqual(result.false_negative_pairs, ((1, 8),))
        self.assertEqual(result.precision, 1.0)
        self.assertEqual(result.recall, 0.5)
        self.assertAlmostEqual(result.f1, 2 / 3)

    def test_empty_ground_truth_and_empty_prediction_is_perfect(self):
        result = evaluate_pairs([], [], sequence_length=10)
        self.assertEqual((result.tp, result.fp, result.fn), (0, 0, 0))
        self.assertEqual((result.precision, result.recall, result.f1), (1.0, 1.0, 1.0))

    def test_empty_ground_truth_with_predictions_is_zero(self):
        result = evaluate_pairs([(0, 9)], [], sequence_length=10)
        self.assertEqual((result.tp, result.fp, result.fn), (0, 1, 0))
        self.assertEqual((result.precision, result.recall, result.f1), (0.0, 0.0, 0.0))

    def test_nonempty_ground_truth_with_empty_prediction_is_zero(self):
        result = evaluate_pairs([], [(0, 9)], sequence_length=10)
        self.assertEqual((result.tp, result.fp, result.fn), (0, 0, 1))
        self.assertEqual((result.precision, result.recall, result.f1), (0.0, 0.0, 0.0))

    def test_crossing_pairs_are_evaluated_exactly(self):
        result = evaluate_pairs(
            [(0, 5), (2, 7)],
            [(0, 5), (2, 7)],
            sequence_length=8,
        )
        self.assertEqual(result.true_positive_pairs, ((0, 5), (2, 7)))
        self.assertEqual((result.tp, result.fp, result.fn), (2, 0, 0))
        self.assertEqual(result.f1, 1.0)

    def test_input_order_does_not_change_result(self):
        first = evaluate_pairs(
            [(4, 5), (0, 9), (1, 8)],
            [(2, 7), (1, 8), (0, 9)],
            sequence_length=10,
        )
        second = evaluate_pairs(
            [(0, 9), (1, 8), (4, 5)],
            [(0, 9), (1, 8), (2, 7)],
            sequence_length=10,
        )
        self.assertEqual(first, second)
        self.assertEqual(first.true_positive_pairs, ((0, 9), (1, 8)))
        self.assertEqual(first.false_positive_pairs, ((4, 5),))
        self.assertEqual(first.false_negative_pairs, ((2, 7),))

    def test_result_can_be_serialized_as_counts_metrics_and_pairs(self):
        result = evaluate_pairs([(0, 5)], [(0, 5), (1, 4)], sequence="ACGUAC")
        self.assertEqual(
            result.as_dict(),
            {
                "tp": 1,
                "fp": 0,
                "fn": 1,
                "precision": 1.0,
                "recall": 0.5,
                "f1": 2 / 3,
            },
        )
        self.assertEqual(result.as_dict(include_pairs=True)["false_negative_pairs"], [[1, 4]])

    def test_evaluator_reuses_pair_validation(self):
        with self.assertRaises(StructureValidationError) as caught:
            evaluate_pairs([(4, 1)], [], sequence_length=5)
        self.assertEqual(caught.exception.code, "reversed_pair")


if __name__ == "__main__":
    unittest.main()
