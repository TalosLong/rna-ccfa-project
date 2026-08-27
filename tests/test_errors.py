import unittest

from rna_ccfa import (
    annotate_missing_pairs,
    extract_false_positive_pairs,
    extract_missing_pairs,
    extract_pair_errors,
    extract_wrong_partner_events,
)


class PairErrorExtractionTests(unittest.TestCase):
    def test_perfect_prediction(self):
        result = extract_pair_errors(
            [(0, 9), (1, 8)],
            [(0, 9), (1, 8)],
            sequence_length=10,
        )
        self.assertEqual(result.missing_pairs, ())
        self.assertEqual(result.false_positive_pairs, ())
        self.assertEqual(result.wrong_partner_events, ())
        self.assertEqual(result.missing_pair_annotations, ())

    def test_pure_missing_pair(self):
        self.assertEqual(
            extract_missing_pairs([], [(0, 9)], sequence_length=10),
            ((0, 9),),
        )
        annotation = annotate_missing_pairs([], [(0, 9)], sequence_length=10)[0]
        self.assertFalse(annotation.wrong_partner)
        self.assertEqual(annotation.wrong_partner_degree, 0)
        self.assertEqual(annotation.linked_false_positive_pairs, ())

    def test_pure_false_positive(self):
        self.assertEqual(
            extract_false_positive_pairs([(0, 9)], [], sequence_length=10),
            ((0, 9),),
        )
        self.assertEqual(
            extract_wrong_partner_events([(0, 9)], [], sequence_length=10),
            (),
        )

    def test_one_endpoint_wrong_partner(self):
        event = extract_wrong_partner_events(
            [(0, 8)],
            [(0, 9)],
            sequence_length=10,
        )[0]
        self.assertEqual(event.predicted_pair, (0, 8))
        self.assertEqual(event.wrong_partner_degree, 1)
        self.assertEqual(
            event.conflicting_endpoints[0].as_dict(),
            {"endpoint": 0, "predicted_partner": 8, "ground_truth_partner": 9},
        )
        self.assertEqual(event.linked_missing_pairs, ((0, 9),))

        annotation = annotate_missing_pairs(
            [(0, 8)],
            [(0, 9)],
            sequence_length=10,
        )[0]
        self.assertTrue(annotation.wrong_partner)
        self.assertEqual(annotation.wrong_partner_degree, 1)
        self.assertEqual(annotation.linked_false_positive_pairs, ((0, 8),))

    def test_two_endpoint_wrong_partner(self):
        event = extract_wrong_partner_events(
            [(0, 8)],
            [(0, 9), (1, 8)],
            sequence_length=10,
        )[0]
        self.assertEqual(event.wrong_partner_degree, 2)
        self.assertEqual(
            tuple(item.endpoint for item in event.conflicting_endpoints),
            (0, 8),
        )
        self.assertEqual(event.linked_missing_pairs, ((0, 9), (1, 8)))

    def test_one_fp_links_to_two_fns(self):
        result = extract_pair_errors(
            [(10, 35)],
            [(10, 40), (20, 35)],
            sequence_length=41,
        )
        self.assertEqual(result.false_positive_pairs, ((10, 35),))
        self.assertEqual(result.missing_pairs, ((10, 40), (20, 35)))
        self.assertEqual(len(result.wrong_partner_events), 1)
        self.assertEqual(
            result.wrong_partner_events[0].linked_missing_pairs,
            result.missing_pairs,
        )
        self.assertTrue(all(item.wrong_partner for item in result.missing_pair_annotations))

    def test_multiple_independent_wrong_partner_events(self):
        events = extract_wrong_partner_events(
            [(0, 8), (2, 6)],
            [(0, 9), (1, 8), (2, 7), (3, 6)],
            sequence_length=10,
        )
        self.assertEqual(tuple(item.predicted_pair for item in events), ((0, 8), (2, 6)))
        self.assertEqual(tuple(item.wrong_partner_degree for item in events), (2, 2))
        self.assertEqual(
            tuple(item.linked_missing_pairs for item in events),
            (((0, 9), (1, 8)), ((2, 7), (3, 6))),
        )

    def test_crossing_pairs_are_ordinary_pairs(self):
        result = extract_pair_errors(
            [(0, 7), (2, 5)],
            [(0, 5), (2, 7)],
            sequence_length=8,
        )
        self.assertEqual(result.missing_pairs, ((0, 5), (2, 7)))
        self.assertEqual(result.false_positive_pairs, ((0, 7), (2, 5)))
        self.assertEqual(
            tuple(event.wrong_partner_degree for event in result.wrong_partner_events),
            (2, 2),
        )
        self.assertEqual(
            tuple(
                annotation.wrong_partner_degree
                for annotation in result.missing_pair_annotations
            ),
            (2, 2),
        )

    def test_input_ordering_independence(self):
        forward = extract_pair_errors(
            [(0, 9), (2, 6), (4, 5)],
            [(0, 9), (2, 7), (3, 6)],
            sequence_length=10,
        )
        reverse = extract_pair_errors(
            [(4, 5), (2, 6), (0, 9)],
            [(3, 6), (2, 7), (0, 9)],
            sequence_length=10,
        )
        self.assertEqual(forward, reverse)


if __name__ == "__main__":
    unittest.main()
