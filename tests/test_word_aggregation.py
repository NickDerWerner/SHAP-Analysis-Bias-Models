"""Unit tests for ARR M1 word aggregation (RoBERTa-style and DeBERTa-style tokens)."""
from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "arr_m1"))

from word_aggregation import (  # noqa: E402
    alignment_ok,
    mass_diagnostics,
    reaggregate_additive,
    reaggregate_charspan,
)


class TestRoBERTaStyleWhitespaceTrailing(unittest.TestCase):
    """shap.maskers.Text often yields tokens like 'A ', 'push '."""

    def setUp(self):
        self.tokens = ["", "A ", "push ", "by ", "Democrats "]
        self.shap = [0.0, 0.1, 0.2, 0.05, 0.3]
        self.text = "A push by Democrats"

    def test_charspan_words(self):
        wa = reaggregate_charspan(self.tokens, self.shap)
        words = [w["word"] for w in wa]
        self.assertEqual(words, ["A", "push", "by", "Democrats"])
        self.assertTrue(alignment_ok(self.text, wa))

    def test_additive_preserves_token_mass(self):
        wa, meta = reaggregate_additive(self.tokens, self.shap)
        words = [w["word"] for w in wa]
        self.assertEqual(words, ["A", "push", "by", "Democrats"])
        # Entire token SHAP lands on words (no pure-whitespace tokens here)
        self.assertAlmostEqual(meta["word_sum"], sum(self.shap[1:]), places=9)
        self.assertAlmostEqual(meta["residual"], 0.0, places=9)


class TestDeBERTaStyleLeadingSpace(unittest.TestCase):
    """DeBERTa-v1 / WordPiece-like: 'Trump', ' has', ' presided'."""

    def setUp(self):
        self.tokens = ["", "Trump", " has", " presided", " over", " economy"]
        self.shap = [0.0, 0.4, 0.1, 0.2, 0.05, 0.25]
        self.text = "Trump has presided over economy"

    def test_charspan_alignment(self):
        wa = reaggregate_charspan(self.tokens, self.shap)
        self.assertEqual(
            [w["word"] for w in wa],
            ["Trump", "has", "presided", "over", "economy"],
        )
        self.assertTrue(alignment_ok(self.text, wa))

    def test_charspan_drops_space_mass(self):
        diag = mass_diagnostics(self.tokens, self.shap)
        # Leading spaces in ' has', ' presided', etc. receive fraction of token SHAP
        self.assertGreater(diag["charspan_drop_frac"], 0.0)
        self.assertAlmostEqual(
            diag["charspan_word_sum"] + diag["charspan_space_mass"],
            diag["token_sum"],
            places=9,
        )

    def test_additive_no_residual(self):
        wa, meta = reaggregate_additive(self.tokens, self.shap)
        self.assertEqual(
            [w["word"] for w in wa],
            ["Trump", "has", "presided", "over", "economy"],
        )
        self.assertAlmostEqual(meta["residual"], 0.0, places=9)
        self.assertAlmostEqual(meta["word_sum"] + meta["whitespace_shap"], meta["token_sum"], places=9)
        # Pure leading-space tokens aren't separate; mass stays on words
        self.assertAlmostEqual(meta["whitespace_shap"], 0.0, places=9)
        self.assertTrue(alignment_ok(self.text, wa))


class TestSubwordContinuation(unittest.TestCase):
    def test_glue_without_space(self):
        tokens = ["erupt", "ing ", "conflict "]
        shap = [0.2, 0.1, 0.3]
        wa, meta = reaggregate_additive(tokens, shap)
        self.assertEqual([w["word"] for w in wa], ["erupting", "conflict"])
        self.assertAlmostEqual(wa[0]["shap"], 0.3, places=9)
        self.assertAlmostEqual(meta["residual"], 0.0, places=9)


class TestSpecialTokensExcluded(unittest.TestCase):
    def test_cls_sep_ignored(self):
        tokens = ["[CLS]", "Hello ", "world", "[SEP]"]
        shap = [0.9, 0.1, 0.2, 0.8]
        wa, meta = reaggregate_additive(tokens, shap)
        self.assertEqual([w["word"] for w in wa], ["Hello", "world"])
        self.assertAlmostEqual(meta["special_shap"], 1.7, places=9)
        self.assertAlmostEqual(meta["token_sum"], 0.3, places=9)


class TestTaxonomyOther(unittest.TestCase):
    def test_other_not_emotional(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "arr_m1"))
        from taxonomy import categorize_word_legacy, categorize_word_v2

        self.assertEqual(categorize_word_v2("Obama"), "Other/Unassigned")
        self.assertEqual(categorize_word_legacy("Obama"), "Emotional/Evaluative")
        self.assertEqual(categorize_word_v2("fierce"), "Emotional/Evaluative")
        self.assertEqual(categorize_word_v2("said"), "Framing/Reporting Verbs")
        self.assertEqual(categorize_word_v2("the"), "Function/Temporal Words")


if __name__ == "__main__":
    unittest.main()
