import csv
import unittest
from pathlib import Path

from rna_ccfa.consolidation import (
    RankedPattern,
    rank_same_unit,
    rate,
    require_fields,
)


ROOT = Path(__file__).resolve().parents[1]


class ConsolidationHelperTests(unittest.TestCase):
    def test_rate_denominator_correctness(self):
        self.assertEqual(rate(2, 5), 0.4)
        for numerator, denominator in ((-1, 5), (6, 5), (0, 0)):
            with self.subTest(numerator=numerator, denominator=denominator):
                with self.assertRaises(ValueError):
                    rate(numerator, denominator)

    def test_cross_unit_or_denominator_ranking_is_rejected(self):
        with self.assertRaises(ValueError):
            rank_same_unit(
                [
                    RankedPattern("pair", 1, 0.1, "pair", "pair_errors"),
                    RankedPattern("stem", 1, 0.1, "stem", "gt_stems"),
                ]
            )
        with self.assertRaises(ValueError):
            rank_same_unit(
                [
                    RankedPattern("fp", 1, 0.1, "pair", "fp"),
                    RankedPattern("fn", 1, 0.1, "pair", "fn"),
                ]
            )

    def test_ties_are_deterministic_by_pattern_name(self):
        patterns = [
            RankedPattern("zeta", 2, 0.5, "pair", "errors"),
            RankedPattern("alpha", 2, 0.5, "pair", "errors"),
        ]
        self.assertEqual(
            [item.name for item in rank_same_unit(patterns)],
            ["alpha", "zeta"],
        )
        self.assertEqual(
            rank_same_unit(patterns), rank_same_unit(tuple(reversed(patterns)))
        )

    def test_missing_values_must_be_explicit(self):
        require_fields({"a": 0, "b": "NA"}, ("a", "b"))
        with self.assertRaises(ValueError):
            require_fields({"a": 1, "b": ""}, ("a", "b"))
        with self.assertRaises(ValueError):
            require_fields({"a": 1}, ("a", "b"))


class ConsolidatedLegacy121RegressionTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / "results/error_analysis/error_summary_by_model.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            self.rows = list(csv.DictReader(handle))

    def test_model_aggregation_and_frozen_counts(self):
        expected = {
            "rnafold": (1473, 220, 203),
            "petfold": (1463, 241, 213),
            "trrosettarna2_native_ss": (1461, 432, 215),
        }
        self.assertEqual({row["source_model"] for row in self.rows}, set(expected))
        for row in self.rows:
            observed = tuple(int(row[key]) for key in ("tp_count", "fp_count", "fn_count"))
            self.assertEqual(observed, expected[row["source_model"]])

        expected_stems = {
            "rnafold": (335, 326, 227, 44, 46, 42),
            "petfold": (335, 312, 203, 42, 48, 44),
            "trrosettarna2_native_ss": (335, 295, 112, 103, 40, 36),
        }
        for row in self.rows:
            observed = tuple(
                int(row[key])
                for key in (
                    "gt_stem_instances",
                    "predicted_stem_instances",
                    "exact_count",
                    "stem_extension_count",
                    "stem_missing_count",
                    "unmatched_predicted_stem_count",
                )
            )
            self.assertEqual(observed, expected_stems[row["source_model"]])

    def test_consolidated_rate_denominators(self):
        for row in self.rows:
            fp, pred = int(row["fp_count"]), int(row["predicted_pair_count"])
            fn, gt = int(row["fn_count"]), int(row["gt_pair_count"])
            self.assertAlmostEqual(float(row["fp_rate_among_predictions"]), fp / pred)
            self.assertAlmostEqual(float(row["fn_rate_among_gt"]), fn / gt)
            self.assertAlmostEqual(
                float(row["fraction_gt_stems_ambiguous"]),
                int(row["ambiguous_gt_stem_count"]) / int(row["gt_stem_instances"]),
            )

    def test_no_implicit_missing_values_or_out_of_range_rates(self):
        for row in self.rows:
            self.assertTrue(all(value != "" for value in row.values()))
            for key, value in row.items():
                if "rate" in key or "fraction" in key:
                    self.assertGreaterEqual(float(value), 0.0)
                    self.assertLessEqual(float(value), 1.0)


if __name__ == "__main__":
    unittest.main()
