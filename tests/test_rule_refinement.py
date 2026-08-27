import unittest

from rna_ccfa import (
    CONDITION_RULES,
    PREREGISTERED_CONDITIONS,
    R1_SINGLETON_DELETE,
    R2_TWO_PAIR_STEM_DELETE,
    R3_OUTER_NONCANONICAL_TRIM,
    DeletionTrigger,
    StructureValidationError,
    detect_incompatible_pair_conflicts,
    merge_deletion_triggers,
    refine_prediction,
    validate_pairs,
)


def sequence_with_pair_types(length, assignments):
    sequence = ["A"] * length
    for pair, pair_type in assignments.items():
        sequence[pair[0]], sequence[pair[1]] = pair_type
    return "".join(sequence)


class FrozenRuleRefinementTests(unittest.TestCase):
    def test_only_preregistered_conditions_are_supported(self):
        self.assertEqual(
            PREREGISTERED_CONDITIONS,
            ("ORIGINAL", "R1", "R2", "R3", "R1_R2", "R1_R3"),
        )
        self.assertEqual(set(CONDITION_RULES), set(PREREGISTERED_CONDITIONS))
        with self.assertRaises(ValueError):
            refine_prediction([], sequence="AAAA", condition="R2_R3")

    def test_singleton_deletion(self):
        result = refine_prediction([(2, 9)], sequence="A" * 12, condition="R1")
        self.assertEqual(result.original_pairs, ((2, 9),))
        self.assertEqual(result.refined_pairs, ())
        self.assertEqual(tuple(edit.deleted_pair for edit in result.edits), ((2, 9),))
        self.assertEqual(result.edits[0].triggering_rule_ids, (R1_SINGLETON_DELETE,))
        self.assertIsNone(result.edits[0].triggers[0].stem_id)

    def test_two_pair_stem_deletion(self):
        pairs = [(2, 11), (3, 10)]
        result = refine_prediction(pairs, sequence="A" * 14, condition="R2")
        self.assertEqual(result.refined_pairs, ())
        self.assertEqual(
            tuple(edit.deleted_pair for edit in result.edits),
            ((2, 11), (3, 10)),
        )
        self.assertTrue(
            all(edit.triggering_rule_ids == (R2_TWO_PAIR_STEM_DELETE,) for edit in result.edits)
        )
        self.assertEqual({edit.triggers[0].stem_id for edit in result.edits}, {"stem_0000"})

    def test_r3_deletes_only_outer_pair(self):
        pairs = [(1, 12), (2, 11), (3, 10)]
        sequence = sequence_with_pair_types(
            14,
            {(1, 12): "AA", (2, 11): "GC", (3, 10): "AU"},
        )
        result = refine_prediction(pairs, sequence=sequence, condition="R3")
        self.assertEqual(result.refined_pairs, ((2, 11), (3, 10)))
        self.assertEqual(tuple(edit.deleted_pair for edit in result.edits), ((1, 12),))
        trigger = result.edits[0].triggers[0]
        self.assertEqual(trigger.rule_id, R3_OUTER_NONCANONICAL_TRIM)
        self.assertEqual(trigger.observable_trigger_features["outer_pair_type"], "AA")
        self.assertEqual(trigger.observable_trigger_features["immediate_inward_pair_type"], "GC")

    def test_all_allowed_wc_wobble_outer_identities_do_not_trigger_r3(self):
        pairs = [(1, 12), (2, 11), (3, 10)]
        for pair_type in ("AU", "UA", "GC", "CG", "GU", "UG"):
            with self.subTest(pair_type=pair_type):
                sequence = sequence_with_pair_types(
                    14,
                    {(1, 12): pair_type, (2, 11): "GC", (3, 10): "AU"},
                )
                result = refine_prediction(pairs, sequence=sequence, condition="R3")
                self.assertEqual(result.refined_pairs, tuple(pairs))
                self.assertEqual(result.edits, ())

    def test_r3_requires_at_least_three_pairs(self):
        pairs = [(1, 10), (2, 9)]
        sequence = sequence_with_pair_types(12, {(1, 10): "AA", (2, 9): "GC"})
        result = refine_prediction(pairs, sequence=sequence, condition="R3")
        self.assertEqual(result.refined_pairs, tuple(pairs))
        self.assertEqual(result.edits, ())

    def test_r3_does_not_cascade_or_reextract(self):
        pairs = [(1, 14), (2, 13), (3, 12), (4, 11)]
        sequence = sequence_with_pair_types(
            16,
            {(1, 14): "AA", (2, 13): "GC", (3, 12): "AU", (4, 11): "GU"},
        )
        result = refine_prediction(pairs, sequence=sequence, condition="R3")
        self.assertEqual(result.refined_pairs, ((2, 13), (3, 12), (4, 11)))
        self.assertEqual(result.modified_pair_count, 1)
        self.assertEqual(result.original_extraction.stems[0].n_pairs, 4)

    def test_combination_collects_simultaneously_from_original_snapshot(self):
        pairs = [(1, 16), (2, 15), (6, 11)]
        result = refine_prediction(pairs, sequence="A" * 18, condition="R1_R2")
        self.assertEqual(result.refined_pairs, ())
        self.assertEqual(
            tuple(edit.deleted_pair for edit in result.edits),
            ((1, 16), (2, 15), (6, 11)),
        )
        self.assertEqual(result.original_extraction.total_pair_count, 3)
        self.assertEqual(len(result.original_extraction.stems), 1)
        self.assertEqual(result.original_extraction.singleton_pairs, ((6, 11),))

    def test_deletion_order_is_deterministic_and_lexicographic(self):
        pairs = [(9, 14), (1, 18), (2, 17), (6, 12)]
        forward = refine_prediction(pairs, sequence="A" * 20, condition="R1_R2")
        reverse = refine_prediction(reversed(pairs), sequence="A" * 20, condition="R1_R2")
        self.assertEqual(forward, reverse)
        self.assertEqual(
            tuple(edit.deleted_pair for edit in forward.edits),
            ((1, 18), (2, 17), (6, 12), (9, 14)),
        )

    def test_one_partner_conflict_detection_and_rejection(self):
        conflicts = detect_incompatible_pair_conflicts(
            [(0, 9), (0, 8)], sequence_length=10
        )
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0].nucleotide, 0)
        self.assertEqual(conflicts[0].partners, (8, 9))
        with self.assertRaises(StructureValidationError) as caught:
            refine_prediction([(0, 9), (0, 8)], sequence="A" * 10, condition="R1")
        self.assertEqual(caught.exception.code, "multiple_partners")

    def test_post_edit_structure_is_valid(self):
        pairs = [(1, 16), (2, 15), (6, 11)]
        result = refine_prediction(pairs, sequence="A" * 18, condition="R1")
        self.assertEqual(
            validate_pairs(result.refined_pairs, sequence_length=18),
            list(result.refined_pairs),
        )

    def test_union_deduplicates_pair_and_preserves_all_rule_ids(self):
        first = DeletionTrigger(
            rule_id=R1_SINGLETON_DELETE,
            deleted_pair=(2, 9),
            observable_trigger_features={"first": True},
            stem_id=None,
        )
        second = DeletionTrigger(
            rule_id=R3_OUTER_NONCANONICAL_TRIM,
            deleted_pair=(2, 9),
            observable_trigger_features={"second": True},
            stem_id="stem_0000",
        )
        edits = merge_deletion_triggers([second, first])
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0].deleted_pair, (2, 9))
        self.assertEqual(
            edits[0].triggering_rule_ids,
            (R1_SINGLETON_DELETE, R3_OUTER_NONCANONICAL_TRIM),
        )
        self.assertEqual(tuple(item.rule_id for item in edits[0].triggers), edits[0].triggering_rule_ids)

    def test_zero_edit_original_and_nontriggering_conditions(self):
        pairs = [(1, 10), (2, 9), (3, 8)]
        sequence = sequence_with_pair_types(
            12,
            {(1, 10): "GC", (2, 9): "AU", (3, 8): "GU"},
        )
        original = refine_prediction(pairs, sequence=sequence, condition="ORIGINAL")
        r1 = refine_prediction(pairs, sequence=sequence, condition="R1")
        r3 = refine_prediction(pairs, sequence=sequence, condition="R3")
        for result in (original, r1, r3):
            self.assertEqual(result.refined_pairs, tuple(pairs))
            self.assertEqual(result.edits, ())


if __name__ == "__main__":
    unittest.main()
