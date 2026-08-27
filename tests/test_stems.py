import unittest

from rna_ccfa import (
    extract_singleton_pairs,
    extract_stems_and_singletons,
    extract_strict_stems,
)


class StrictStemExtractionTests(unittest.TestCase):
    def test_empty_pair_set(self):
        result = extract_stems_and_singletons([], sequence_length=25)
        self.assertEqual(result.stems, ())
        self.assertEqual(result.singleton_pairs, ())
        self.assertEqual(result.total_pair_count, 0)

    def test_one_singleton_pair(self):
        result = extract_stems_and_singletons([(3, 20)], sequence_length=25)
        self.assertEqual(result.stems, ())
        self.assertEqual(result.singleton_pairs, ((3, 20),))

    def test_two_pair_stem(self):
        stems = extract_strict_stems([(4, 19), (3, 20)], sequence_length=25)
        self.assertEqual(len(stems), 1)
        stem = stems[0]
        self.assertEqual(stem.pairs, ((3, 20), (4, 19)))
        self.assertEqual(stem.n_pairs, 2)
        self.assertEqual(stem.outer_pair, (3, 20))
        self.assertEqual(stem.inner_pair, (4, 19))
        self.assertEqual((stem.left_start, stem.left_end), (3, 4))
        self.assertEqual((stem.right_start, stem.right_end), (19, 20))

    def test_longer_stem(self):
        stem = extract_strict_stems(
            [(5, 18), (3, 20), (4, 19)],
            sequence_length=25,
        )[0]
        self.assertEqual(stem.pairs, ((3, 20), (4, 19), (5, 18)))
        self.assertEqual(stem.n_pairs, 3)
        self.assertEqual(stem.outer_pair, (3, 20))
        self.assertEqual(stem.inner_pair, (5, 18))
        self.assertEqual(
            (stem.left_start, stem.left_end, stem.right_start, stem.right_end),
            (3, 5, 18, 20),
        )

    def test_multiple_independent_stems(self):
        result = extract_stems_and_singletons(
            [(6, 14), (1, 10), (5, 15), (2, 9)],
            sequence_length=20,
        )
        self.assertEqual(
            tuple(stem.outer_pair for stem in result.stems),
            ((1, 10), (5, 15)),
        )
        self.assertEqual(result.singleton_pairs, ())

    def test_stems_plus_singleton_pairs(self):
        result = extract_stems_and_singletons(
            [(3, 20), (4, 19), (1, 8)],
            sequence_length=25,
        )
        self.assertEqual(len(result.stems), 1)
        self.assertEqual(result.singleton_pairs, ((1, 8),))
        self.assertEqual(
            sum(stem.n_pairs for stem in result.stems) + len(result.singleton_pairs),
            result.total_pair_count,
        )

    def test_crossing_stems_are_independent(self):
        result = extract_stems_and_singletons(
            [(5, 10), (1, 8), (4, 11), (2, 7)],
            sequence_length=15,
        )
        self.assertEqual(
            tuple(stem.pairs for stem in result.stems),
            (((1, 8), (2, 7)), ((4, 11), (5, 10))),
        )
        self.assertEqual(result.singleton_pairs, ())

    def test_gap_does_not_bridge(self):
        result = extract_stems_and_singletons(
            [(3, 20), (5, 18)],
            sequence_length=25,
        )
        self.assertEqual(result.stems, ())
        self.assertEqual(result.singleton_pairs, ((3, 20), (5, 18)))

    def test_neighboring_but_nonstacked_pairs_do_not_merge(self):
        result = extract_stems_and_singletons(
            [(3, 20), (4, 18)],
            sequence_length=25,
        )
        self.assertEqual(result.stems, ())
        self.assertEqual(result.singleton_pairs, ((3, 20), (4, 18)))

    def test_complete_pair_accounting(self):
        pairs = [(1, 10), (2, 9), (4, 15), (7, 18), (8, 17)]
        result = extract_stems_and_singletons(pairs, sequence_length=20)
        self.assertEqual(
            sum(stem.n_pairs for stem in result.stems) + len(result.singleton_pairs),
            len(pairs),
        )
        self.assertEqual(
            set(result.singleton_pairs)
            | {pair for stem in result.stems for pair in stem.pairs},
            set(pairs),
        )

    def test_input_ordering_and_canonical_stem_ordering(self):
        pairs = [(7, 18), (2, 9), (5, 15), (1, 10), (6, 14)]
        forward = extract_stems_and_singletons(pairs, sequence_length=20)
        reverse = extract_stems_and_singletons(list(reversed(pairs)), sequence_length=20)
        self.assertEqual(forward, reverse)
        self.assertEqual(
            tuple(stem.outer_pair for stem in forward.stems),
            ((1, 10), (5, 15)),
        )
        self.assertEqual(forward.singleton_pairs, ((7, 18),))

    def test_singleton_helper_matches_complete_extraction(self):
        pairs = [(3, 20), (4, 19), (9, 12)]
        result = extract_stems_and_singletons(pairs, sequence_length=25)
        self.assertEqual(
            extract_singleton_pairs(pairs, sequence_length=25),
            result.singleton_pairs,
        )


if __name__ == "__main__":
    unittest.main()
