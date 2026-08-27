import unittest

from rna_ccfa.separation import (
    LEGACY121_RELATIVE_THRESHOLDS,
    LEGACY121_SEPARATION_BINS,
    assign_legacy121_separation_bin,
    pair_separation,
)


class PairSeparationTests(unittest.TestCase):
    def test_raw_and_relative_definitions(self):
        value = pair_separation((2, 8), 11)
        self.assertEqual(value.sequence_separation, 6)
        self.assertEqual(value.relative_separation, 0.6)

    def test_full_span_pair_has_relative_separation_one(self):
        value = pair_separation((0, 1), 2)
        self.assertEqual(value.sequence_separation, 1)
        self.assertEqual(value.relative_separation, 1.0)

    def test_invalid_pair_or_length_is_rejected(self):
        for pair, length in [((0, 0), 2), ((1, 0), 2), ((0, 2), 2), ((0, 1), 1)]:
            with self.subTest(pair=pair, length=length):
                with self.assertRaises(ValueError):
                    pair_separation(pair, length)

    def test_threshold_values_belong_to_lower_bin(self):
        for threshold, label in zip(
            LEGACY121_RELATIVE_THRESHOLDS,
            LEGACY121_SEPARATION_BINS,
        ):
            with self.subTest(threshold=threshold):
                self.assertEqual(assign_legacy121_separation_bin(threshold), label)

    def test_all_frozen_bins_and_long_range_boundary(self):
        values = (0.1, 0.3, 0.6, 0.9, 0.95)
        self.assertEqual(
            tuple(assign_legacy121_separation_bin(value) for value in values),
            LEGACY121_SEPARATION_BINS,
        )
        self.assertNotEqual(
            assign_legacy121_separation_bin(LEGACY121_RELATIVE_THRESHOLDS[-1]),
            LEGACY121_SEPARATION_BINS[-1],
        )

    def test_invalid_relative_value_is_rejected(self):
        for value in (0.0, -0.1, 1.1, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    assign_legacy121_separation_bin(value)


if __name__ == "__main__":
    unittest.main()
