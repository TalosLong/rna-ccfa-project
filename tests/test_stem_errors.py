import unittest

from rna_ccfa.stem_errors import analyze_stem_errors, classify_isolated_stem_match, compute_stem_relation
from rna_ccfa.stems import extract_strict_stems


def pairs(start, end, n): return [(start + k, end - k) for k in range(n)]


class StemErrorTests(unittest.TestCase):
    def test_exact_and_boundaries(self):
        gt = pairs(10, 40, 4)
        for pred, state, subtype in [(gt[1:], "stem_truncation", "outer"), (gt[:-1], "stem_truncation", "inner"), (gt[1:-1], "stem_truncation", "both")]:
            a = analyze_stem_errors(gt, pred, sequence_length=50)
            self.assertEqual((a.isolated_matches[0].state, a.isolated_matches[0].boundary_subtype), (state, subtype))
        for pred, state, subtype in [(pairs(9,41,5), "stem_extension", "outer"), (pairs(10,40,5), "stem_extension", "inner")]:
            a = analyze_stem_errors(gt, pred, sequence_length=50)
            self.assertEqual((a.isolated_matches[0].state, a.isolated_matches[0].boundary_subtype), (state, subtype))
        a = analyze_stem_errors(gt, gt, sequence_length=50)
        self.assertEqual(a.isolated_matches[0].state, "exact")

    def test_shift_and_mixed_boundary(self):
        gt = pairs(10, 40, 4)
        self.assertEqual(analyze_stem_errors(gt, [(11,40),(12,39),(13,38)], sequence_length=50).isolated_matches[0].state, "stem_shift")
        self.assertEqual(analyze_stem_errors(gt, [(11,41),(12,40),(13,39),(14,38)], sequence_length=50).isolated_matches[0].state, "stem_shift")
        self.assertEqual(analyze_stem_errors(gt, pairs(11,39,4), sequence_length=50).isolated_matches[0].state, "complex_mismatch")

    def test_residuals_and_ambiguous_components(self):
        a = analyze_stem_errors(pairs(0,20,2), [], sequence_length=30)
        self.assertEqual(len(a.missing_gt_indices), 1)
        a = analyze_stem_errors([], pairs(0,20,2), sequence_length=30)
        self.assertEqual(len(a.unmatched_pred_indices), 1)
        gt = pairs(0,20,2) + pairs(5,15,2)
        pred = pairs(0,20,7)
        a = analyze_stem_errors(gt, pred, sequence_length=30)
        self.assertEqual(len(a.ambiguous_components), 1)
        self.assertEqual(len(a.isolated_matches), 0)

    def test_crossing_and_order_independence(self):
        gt = [(1,8),(2,7),(4,11),(5,10)]
        a = analyze_stem_errors(gt, list(reversed(gt)), sequence_length=20)
        self.assertEqual([m.state for m in a.isolated_matches], ["exact", "exact"])
        b = analyze_stem_errors(list(reversed(gt)), gt, sequence_length=20)
        self.assertEqual(a, b)

    def test_accounting(self):
        gt = pairs(0,20,3) + [(30,39)]
        pred = pairs(0,20,2) + [(31,38)]
        a = analyze_stem_errors(gt, pred, sequence_length=50)
        self.assertEqual(len(a.gt_stems), 1); self.assertEqual(len(a.predicted_stems), 1)
        self.assertEqual(sum(1 for _ in a.isolated_matches) + len(a.missing_gt_indices), len(a.gt_stems))


if __name__ == "__main__": unittest.main()
