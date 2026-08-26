import unittest

from rna_ccfa import (
    StructureValidationError,
    parse_dense_matrix,
    parse_dot_bracket,
    parse_pair_list,
    parse_standard_dot_bracket,
    parse_structure,
    validate_pairs,
)


class StructureParserTests(unittest.TestCase):
    def assert_validation_code(self, code, function, *args, **kwargs):
        with self.assertRaises(StructureValidationError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_simple_nested_structure(self):
        self.assertEqual(
            parse_standard_dot_bracket("((...))", sequence_length=7),
            [(0, 6), (1, 5)],
        )

    def test_completely_unpaired_structure(self):
        self.assertEqual(parse_dot_bracket("......", sequence="ACGUAC"), [])

    def test_multiple_stems_are_sorted_canonically(self):
        self.assertEqual(
            parse_standard_dot_bracket("(())..(())"),
            [(0, 3), (1, 2), (6, 9), (7, 8)],
        )

    def test_extended_brackets_preserve_crossing_pairs(self):
        self.assertEqual(parse_dot_bracket("([)]"), [(0, 2), (1, 3)])

    def test_all_extended_symbol_families(self):
        self.assertEqual(
            parse_dot_bracket("([{<Aa>}])"),
            [(0, 9), (1, 8), (2, 7), (3, 6), (4, 5)],
        )

    def test_standard_parser_rejects_extended_symbols(self):
        self.assert_validation_code(
            "illegal_structure_character",
            parse_standard_dot_bracket,
            "[.]",
        )

    def test_unmatched_closing_bracket(self):
        self.assert_validation_code("unmatched_bracket", parse_dot_bracket, ".)")

    def test_unmatched_opening_bracket(self):
        self.assert_validation_code("unmatched_bracket", parse_dot_bracket, "((.")

    def test_mismatched_bracket_family_is_unmatched(self):
        self.assert_validation_code("unmatched_bracket", parse_dot_bracket, "(]")

    def test_illegal_structure_character(self):
        self.assert_validation_code(
            "illegal_structure_character",
            parse_dot_bracket,
            ".-.",
        )

    def test_sequence_structure_length_mismatch(self):
        self.assert_validation_code(
            "length_mismatch",
            parse_dot_bracket,
            "....",
            sequence="ACGUA",
        )

    def test_pair_list_is_sorted_without_reordering_endpoints(self):
        self.assertEqual(
            parse_pair_list([(3, 5), (0, 2)], sequence_length=6),
            [(0, 2), (3, 5)],
        )

    def test_one_based_pair_list_converts_to_zero_based(self):
        self.assertEqual(
            parse_pair_list([(2, 5), (1, 6)], sequence_length=6, index_base=1),
            [(0, 5), (1, 4)],
        )

    def test_duplicate_pairs_are_rejected(self):
        self.assert_validation_code(
            "duplicate_pair",
            parse_pair_list,
            [(0, 3), (0, 3)],
            sequence_length=4,
        )

    def test_conflicting_partners_are_rejected_by_default(self):
        self.assert_validation_code(
            "multiple_partners",
            parse_pair_list,
            [(0, 3), (0, 4)],
            sequence_length=5,
        )

    def test_multiple_partners_can_be_explicitly_allowed(self):
        self.assertEqual(
            parse_pair_list(
                [(0, 4), (0, 3)],
                sequence_length=5,
                allow_multiple_partners=True,
            ),
            [(0, 3), (0, 4)],
        )

    def test_self_pair_is_rejected(self):
        self.assert_validation_code(
            "self_pair", validate_pairs, [(2, 2)], sequence_length=4
        )

    def test_reversed_pair_is_rejected(self):
        self.assert_validation_code(
            "reversed_pair", validate_pairs, [(3, 1)], sequence_length=4
        )

    def test_out_of_range_pair_is_rejected(self):
        self.assert_validation_code(
            "out_of_range_pair", validate_pairs, [(0, 4)], sequence_length=4
        )

    def test_dense_matrix_conversion(self):
        matrix = [
            [0, 0, 0, 1],
            [0, 0, 1, 0],
            [0, 1, 0, 0],
            [1, 0, 0, 0],
        ]
        self.assertEqual(
            parse_dense_matrix(matrix, sequence="ACGU"),
            [(0, 3), (1, 2)],
        )

    def test_dense_matrix_preserves_crossing_pairs(self):
        matrix = [
            [0, 0, 1, 0],
            [0, 0, 0, 1],
            [1, 0, 0, 0],
            [0, 1, 0, 0],
        ]
        self.assertEqual(parse_dense_matrix(matrix), [(0, 2), (1, 3)])

    def test_dense_matrix_must_be_symmetric(self):
        self.assert_validation_code(
            "asymmetric_matrix",
            parse_dense_matrix,
            [[0, 1], [0, 0]],
        )

    def test_dense_matrix_rejects_nonzero_diagonal(self):
        self.assert_validation_code(
            "self_pair",
            parse_dense_matrix,
            [[1, 0], [0, 0]],
        )

    def test_dense_matrix_rejects_nonbinary_values(self):
        self.assert_validation_code(
            "invalid_matrix_value",
            parse_dense_matrix,
            [[0, 0.5], [0.5, 0]],
        )

    def test_dense_matrix_length_mismatch(self):
        self.assert_validation_code(
            "length_mismatch",
            parse_dense_matrix,
            [[0, 0], [0, 0]],
            sequence_length=3,
        )

    def test_generic_dispatch_uses_schema_format_names(self):
        self.assertEqual(
            parse_structure("([)]", "extended_dot_bracket", sequence_length=4),
            [(0, 2), (1, 3)],
        )


if __name__ == "__main__":
    unittest.main()
