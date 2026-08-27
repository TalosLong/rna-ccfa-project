import unittest

from rna_ccfa import extract_strict_stems
from scripts.audit_legacy121_stem_matching_candidates import (
    FINAL_CANDIDATE_FILTER,
    _ambiguous_component_counts,
    candidate_metrics,
    is_candidate,
    potential_shift_evidence,
)


class StemMatchingCandidateAuditTests(unittest.TestCase):
    @staticmethod
    def _stem(pairs, sequence_length=50):
        stems = extract_strict_stems(pairs, sequence_length=sequence_length)
        if len(stems) != 1:
            raise AssertionError("test fixture must contain exactly one strict stem")
        return stems[0]

    def setUp(self):
        self.gt = self._stem(
            [(10, 40), (11, 39), (12, 38), (13, 37)]
        )

    def test_case_a_has_positive_shift_evidence(self):
        predicted = self._stem([(11, 40), (12, 39), (13, 38)])
        metrics = candidate_metrics(self.gt, predicted)
        self.assertEqual(metrics.exact_pair_overlap, 0)
        self.assertEqual((metrics.left_arm_overlap, metrics.right_arm_overlap), (3, 3))
        self.assertEqual(metrics.register_delta, 1)
        self.assertTrue(potential_shift_evidence(metrics, FINAL_CANDIDATE_FILTER))

    def test_case_b_has_positive_shift_evidence(self):
        predicted = self._stem(
            [(11, 41), (12, 40), (13, 39), (14, 38)]
        )
        metrics = candidate_metrics(self.gt, predicted)
        self.assertEqual(metrics.exact_pair_overlap, 0)
        self.assertEqual((metrics.left_arm_overlap, metrics.right_arm_overlap), (3, 3))
        self.assertEqual(metrics.register_delta, 2)
        self.assertTrue(potential_shift_evidence(metrics, FINAL_CANDIDATE_FILTER))

    def test_case_c_is_not_shift_evidence(self):
        predicted = self._stem(
            [(11, 39), (12, 38), (13, 37), (14, 36)]
        )
        metrics = candidate_metrics(self.gt, predicted)
        self.assertEqual(metrics.exact_pair_overlap, 3)
        self.assertEqual(metrics.register_delta, 0)
        self.assertFalse(potential_shift_evidence(metrics, FINAL_CANDIDATE_FILTER))
        self.assertTrue(is_candidate(metrics, FINAL_CANDIDATE_FILTER))

    def test_one_nucleotide_bilateral_rule_is_rejected_by_final_filter(self):
        predicted = self._stem([(13, 40), (14, 39)])
        metrics = candidate_metrics(self.gt, predicted)
        self.assertEqual(metrics.exact_pair_overlap, 0)
        self.assertEqual(metrics.minimum_arm_overlap, 1)
        self.assertTrue(potential_shift_evidence(metrics, "bilateral_at_least_1"))
        self.assertFalse(potential_shift_evidence(metrics, FINAL_CANDIDATE_FILTER))

    def test_multi_stem_candidate_component_is_detected(self):
        gt_stems = extract_strict_stems(
            [(0, 9), (1, 8), (3, 6), (4, 5)],
            sequence_length=10,
        )
        predicted = self._stem(
            [(0, 9), (1, 8), (2, 7), (3, 6), (4, 5)],
            sequence_length=10,
        )
        edges = [
            (index, 0, candidate_metrics(gt, predicted))
            for index, gt in enumerate(gt_stems)
        ]
        count, ambiguous_gt, ambiguous_pred = _ambiguous_component_counts(
            len(gt_stems), 1, edges
        )
        self.assertEqual(count, 1)
        self.assertEqual(ambiguous_gt, {0, 1})
        self.assertEqual(ambiguous_pred, {0})


if __name__ == "__main__":
    unittest.main()
