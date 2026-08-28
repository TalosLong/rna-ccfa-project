import unittest

from rna_ccfa.cross_model import cross_model_agreement_features


class CrossModelAgreementTests(unittest.TestCase):
    def test_exact_support_and_partner_conflict(self):
        predictions = {
            "rnafold": [(0, 5), (1, 4)],
            "petfold": [(0, 5), (1, 3)],
            "trrosettarna2_native_ss": [(0, 4), (1, 3)],
        }
        row = cross_model_agreement_features("rnafold", (0, 5), predictions, sequence_length=6)
        self.assertEqual(row["exact_support_other_count"], 1)
        self.assertEqual(row["endpoint_i_conflict_count"], 1)
        self.assertEqual(row["any_partner_conflict"], 1)
        self.assertEqual(row["support_by_rnafold"], 0)

    def test_complete_matrix_is_required(self):
        with self.assertRaises(ValueError):
            cross_model_agreement_features("rnafold", (0, 3), {"rnafold": [(0, 3)]}, sequence_length=4)


if __name__ == "__main__":
    unittest.main()
