import unittest

from scripts.evaluate_legacy121_rule_baseline import _outcome


class PilotOutcomeTests(unittest.TestCase):
    def test_reference_condition(self):
        self.assertEqual(
            _outcome(
                condition="ORIGINAL",
                modified=0,
                beneficial=0,
                harmful=0,
                macro_delta_f1=0.0,
                micro_delta_f1=0.0,
            ),
            "REFERENCE",
        )

    def test_useful_signal_requires_both_macro_and_micro_f1_gain(self):
        self.assertEqual(
            _outcome(
                condition="R1",
                modified=10,
                beneficial=8,
                harmful=2,
                macro_delta_f1=0.01,
                micro_delta_f1=0.02,
            ),
            "USEFUL SIGNAL",
        )
        self.assertEqual(
            _outcome(
                condition="R1",
                modified=10,
                beneficial=8,
                harmful=2,
                macro_delta_f1=-0.01,
                micro_delta_f1=0.02,
            ),
            "TRADE-OFF",
        )

    def test_no_edit_or_nonmajority_beneficial_is_no_signal(self):
        self.assertEqual(
            _outcome(
                condition="R3",
                modified=0,
                beneficial=0,
                harmful=0,
                macro_delta_f1=0.0,
                micro_delta_f1=0.0,
            ),
            "NO USEFUL SIGNAL",
        )
        self.assertEqual(
            _outcome(
                condition="R2",
                modified=8,
                beneficial=4,
                harmful=4,
                macro_delta_f1=0.01,
                micro_delta_f1=0.01,
            ),
            "NO USEFUL SIGNAL",
        )


if __name__ == "__main__":
    unittest.main()
