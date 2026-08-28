import copy
import inspect
import unittest

from rna_ccfa.simulated_evidence import (
    EVIDENCE_SEEDS,
    POSITIVE_PAIR_EVIDENCE,
    UNPAIRED_NUCLEOTIDE_EVIDENCE,
    EvidenceValidationError,
    apply_pair_hard_enforce,
    apply_pair_protect_only,
    apply_unpaired_hard_delete,
    build_clean_evidence_manifest,
    corrupt_evidence_manifest,
    pair_evidence_universe,
    round_half_up_count,
    unpaired_evidence_universe,
    validate_evidence_manifest,
    validate_generator_input_fields,
)


class SimulatedEvidenceTests(unittest.TestCase):
    def test_universes_are_gt_only_and_sorted(self):
        sequence = "GCAAAUGC"
        pairs = [(0, 7), (1, 6)]
        self.assertEqual(pair_evidence_universe(sequence, pairs), tuple(pairs))
        self.assertEqual(unpaired_evidence_universe(sequence, pairs), (2, 3, 4, 5))

    def test_round_half_up_and_minimum_one(self):
        self.assertEqual(round_half_up_count(10, 5, minimum_one=False), 1)
        self.assertEqual(round_half_up_count(9, 5, minimum_one=False), 0)
        self.assertEqual(round_half_up_count(9, 5, minimum_one=True), 1)
        self.assertEqual(round_half_up_count(0, 50, minimum_one=True), 0)
        self.assertEqual(round_half_up_count(20, 0, minimum_one=True), 0)

    def test_clean_sampling_is_deterministic(self):
        kwargs = dict(
            rna_id="rna",
            sequence="GCAAAUGC",
            ground_truth_pairs=[(0, 7), (1, 6)],
            evidence_channel=UNPAIRED_NUCLEOTIDE_EVIDENCE,
            density_percent=50,
            evidence_seed=EVIDENCE_SEEDS[0],
        )
        first = build_clean_evidence_manifest(**kwargs)
        second = build_clean_evidence_manifest(**kwargs)
        self.assertEqual(first, second)
        self.assertEqual(first["selected_item_count"], 2)
        self.assertEqual(first["manifest_payload_sha256"], second["manifest_payload_sha256"])

    def test_pair_corruption_preserves_one_endpoint_and_is_false(self):
        sequence = "GCGCAUAUAAAA"
        pairs = [(0, 1), (2, 3), (4, 5), (6, 7)]
        clean = build_clean_evidence_manifest(
            rna_id="pair_corruption",
            sequence=sequence,
            ground_truth_pairs=pairs,
            evidence_channel=POSITIVE_PAIR_EVIDENCE,
            density_percent=50,
            evidence_seed=101,
        )
        corrupted = corrupt_evidence_manifest(
            clean,
            sequence=sequence,
            ground_truth_pairs=pairs,
            noise_level_percent=30,
        )
        self.assertEqual(
            corrupted,
            corrupt_evidence_manifest(
                clean,
                sequence=sequence,
                ground_truth_pairs=pairs,
                noise_level_percent=30,
            ),
        )
        self.assertEqual(corrupted["requested_corruption_count"], 1)
        changed = [item for item in corrupted["items"] if item["status"] == "CORRUPTED"]
        self.assertEqual(len(changed), 1)
        original = set(changed[0]["original_clean_evidence_item"].values())
        delivered = set(changed[0]["delivered_evidence_item"].values())
        self.assertEqual(len(original & delivered), 1)
        self.assertNotIn(tuple(changed[0]["delivered_evidence_item"].values()), pairs)

    def test_unpaired_corruption_delivers_gt_paired_position(self):
        sequence = "GCAAAUGC"
        pairs = [(0, 7), (1, 6)]
        clean = build_clean_evidence_manifest(
            rna_id="unpaired_corruption",
            sequence=sequence,
            ground_truth_pairs=pairs,
            evidence_channel=UNPAIRED_NUCLEOTIDE_EVIDENCE,
            density_percent=50,
            evidence_seed=101,
        )
        corrupted = corrupt_evidence_manifest(
            clean,
            sequence=sequence,
            ground_truth_pairs=pairs,
            noise_level_percent=30,
        )
        paired = {0, 1, 6, 7}
        changed = [item for item in corrupted["items"] if item["status"] == "CORRUPTED"]
        self.assertEqual(len(changed), 1)
        self.assertIn(changed[0]["delivered_evidence_item"]["i"], paired)

    def test_manifest_hash_tampering_fails(self):
        manifest = build_clean_evidence_manifest(
            rna_id="rna",
            sequence="GCAAAUGC",
            ground_truth_pairs=[(0, 7), (1, 6)],
            evidence_channel=POSITIVE_PAIR_EVIDENCE,
            density_percent=50,
            evidence_seed=101,
        )
        tampered = copy.deepcopy(manifest)
        tampered["density_percent"] = 20
        with self.assertRaises(EvidenceValidationError):
            validate_evidence_manifest(
                tampered,
                sequence="GCAAAUGC",
                ground_truth_pairs=[(0, 7), (1, 6)],
            )

    def test_generator_input_contract_rejects_prediction_fields(self):
        expected = {"rna_id", "sequence", "ground_truth_pairs"}
        self.assertEqual(set(inspect.signature(build_clean_evidence_manifest).parameters) - {"evidence_channel", "density_percent", "evidence_seed", "protocol_version"}, expected)
        validate_generator_input_fields(expected)
        with self.assertRaises(EvidenceValidationError):
            validate_generator_input_fields(expected | {"predicted_structure"})

    def test_hard_transformations_are_local_and_valid(self):
        prediction = [(0, 7), (1, 5), (2, 4)]
        evidence = [(1, 6)]
        self.assertEqual(
            apply_pair_protect_only(prediction, evidence, sequence_length=8),
            [(0, 7), (2, 4)],
        )
        self.assertEqual(
            apply_pair_hard_enforce(prediction, evidence, sequence_length=8),
            [(0, 7), (1, 6), (2, 4)],
        )
        self.assertEqual(
            apply_unpaired_hard_delete(prediction, [2], sequence_length=8),
            [(0, 7), (1, 5)],
        )


if __name__ == "__main__":
    unittest.main()
