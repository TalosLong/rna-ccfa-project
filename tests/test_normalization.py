import tempfile
import unittest
from pathlib import Path

import numpy as np

from rna_ccfa.normalization import (
    NormalizationError,
    filesystem_slug,
    make_record_id,
    normalize_probability_matrix_diagonal,
    sha256_file,
    validate_normalized_probability_matrix,
    validate_normalized_sequence,
)


class NormalizationTests(unittest.TestCase):
    def test_record_id_uses_schema_layout_and_slugs(self):
        self.assertEqual(
            make_record_id(
                "Legacy121 v1",
                "1A9L_38_hpbulge_nmr_A",
                "legacy_gt",
                "RNAfold",
                "historical_v1",
            ),
            "legacy121_v1__1a9l_38_hpbulge_nmr_a__legacy_gt__rnafold__historical_v1",
        )
        self.assertEqual(filesystem_slug("trRosettaRNA2 native SS"), "trrosettarna2_native_ss")

    def test_normalized_sequence_validation(self):
        validate_normalized_sequence("ACGURYSWKMBDHVN")
        for invalid in ("", "acgu", "AC GU", "ACGT"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(NormalizationError):
                    validate_normalized_sequence(invalid)

    def test_set_diagonal_to_zero_preserves_every_off_diagonal_value(self):
        raw = np.array(
            [
                [0.01, 0.20, 0.30],
                [0.20, 0.02, 0.40],
                [0.30, 0.40, 0.03],
            ],
            dtype=np.float32,
        )
        raw_before = raw.copy()

        normalized, stats = normalize_probability_matrix_diagonal(raw, expected_length=3)

        self.assertTrue(np.array_equal(raw, raw_before))
        self.assertEqual(normalized.dtype, raw.dtype)
        self.assertTrue(np.array_equal(np.diag(normalized), np.zeros(3, dtype=np.float32)))
        mask = ~np.eye(3, dtype=bool)
        self.assertTrue(np.array_equal(normalized[mask], raw[mask]))
        self.assertEqual(stats.diagonal_nonzero_count_before, 3)
        self.assertAlmostEqual(stats.diagonal_min_before, 0.01, places=6)
        self.assertAlmostEqual(stats.diagonal_max_before, 0.03, places=6)
        self.assertEqual(stats.diagonal_nonzero_count_after, 0)
        self.assertEqual(stats.max_off_diagonal_absolute_change, 0.0)
        validate_normalized_probability_matrix(normalized, expected_length=3)

    def test_asymmetric_raw_matrix_is_rejected(self):
        raw = np.array([[0.0, 0.2], [0.3, 0.0]], dtype=np.float32)
        with self.assertRaises(NormalizationError):
            normalize_probability_matrix_diagonal(raw, expected_length=2)

    def test_invalid_probability_values_are_rejected(self):
        invalid_matrices = (
            np.array([[0.0, -0.1], [-0.1, 0.0]], dtype=np.float32),
            np.array([[0.0, 1.1], [1.1, 0.0]], dtype=np.float32),
            np.array([[0.0, np.nan], [np.nan, 0.0]], dtype=np.float32),
        )
        for matrix in invalid_matrices:
            with self.subTest(matrix=matrix):
                with self.assertRaises(NormalizationError):
                    normalize_probability_matrix_diagonal(matrix, expected_length=2)

    def test_shape_mismatch_is_rejected(self):
        matrix = np.zeros((2, 2), dtype=np.float32)
        with self.assertRaises(NormalizationError):
            normalize_probability_matrix_diagonal(matrix, expected_length=3)

    def test_normalized_validation_rejects_nonzero_diagonal(self):
        matrix = np.array([[0.01, 0.2], [0.2, 0.0]], dtype=np.float32)
        with self.assertRaises(NormalizationError):
            validate_normalized_probability_matrix(matrix, expected_length=2)

    def test_sha256_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.txt"
            path.write_bytes(b"rna-ccfa")
            self.assertEqual(
                sha256_file(path),
                "35a5933c8f25b712b65323fec2ae69c52578840816c003c2d3e9fdd1aa7c9124",
            )


if __name__ == "__main__":
    unittest.main()
