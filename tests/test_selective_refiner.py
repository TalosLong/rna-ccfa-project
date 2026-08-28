import unittest

from rna_ccfa.selective_refiner import extract_feature_rows


class SelectiveRefinerFeatureTests(unittest.TestCase):
    def test_labels_and_frozen_observable_schema(self):
        rows = extract_feature_rows("x", "GCAU", [(0, 3), (1, 2)], [(0, 3)], "rnafold", True)
        self.assertEqual([r.label for r in rows], [0, 1])
        self.assertNotIn("ground_truth", rows[0].features)
        self.assertNotIn("gt_partner", rows[0].features)
        self.assertEqual(rows[0].features["raw_separation"], 3)

    def test_one_partner_and_coordinate_validation(self):
        with self.assertRaises(ValueError):
            extract_feature_rows("x", "GCAU", [(0, 3), (0, 2)], [], "rnafold", False)
        with self.assertRaises(ValueError):
            extract_feature_rows("x", "GCAU", [(0, 4)], [], "rnafold", False)


if __name__ == "__main__":
    unittest.main()
