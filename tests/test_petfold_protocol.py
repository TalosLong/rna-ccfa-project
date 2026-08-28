import unittest

from rna_ccfa.structure import StructureValidationError
from scripts.reproduce_petfold import petfold_pairs, structure_from_stdout


class PETfoldProtocolTests(unittest.TestCase):
    def test_structure_extraction_uses_final_petfold_line(self):
        stdout = (
            "Pfold RNA structure:\t((..))\n"
            "PETfold RNA structure:\t((..))\n"
            "Score_{model,structure}{tree,alignment} = 0.5\n"
        )
        self.assertEqual(structure_from_stdout(stdout), "((..))")

    def test_single_sequence_coordinates_are_zero_based(self):
        self.assertEqual(petfold_pairs("((..))", "ACGUAC"), [(0, 5), (1, 4)])

    def test_coordinate_length_mismatch_is_rejected(self):
        with self.assertRaises(StructureValidationError):
            petfold_pairs("((..))", "ACGUA")
