"""Unit tests for ARR M2 perturbation selection and masking."""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "arr_m2"))

from perturbations import (  # noqa: E402
    apply_mask,
    count_changed_whitespace_tokens,
    locate_word_span,
    select_words,
)


class TestLocateAndMask(unittest.TestCase):
    def test_exact_locate(self):
        text = "A push by Democrats to loosen rules"
        span = locate_word_span(text, "Democrats")
        self.assertIsNotNone(span)
        self.assertEqual(text[span.start : span.end], "Democrats")

    def test_mask_replaces_budget_words(self):
        text = "Fierce criticism followed the claim yesterday"
        was = [
            {"word": "Fierce", "shap": 0.4},
            {"word": "claim", "shap": 0.2},
            {"word": "yesterday", "shap": 0.01},
        ]
        new, meta = apply_mask(text, was[:2], "<mask>")
        self.assertEqual(meta["n_applied"], 2)
        self.assertEqual(meta["n_failed"], 0)
        self.assertEqual(new.count("<mask>"), 2)
        self.assertNotIn("Fierce", new.split())
        self.assertIn("followed", new)

    def test_failed_align_recorded(self):
        text = "Hello world"
        new, meta = apply_mask(text, [{"word": "xyzzy", "shap": 1.0}], "<mask>")
        self.assertEqual(meta["n_applied"], 0)
        self.assertEqual(meta["n_failed"], 1)
        self.assertEqual(new, text)

    def test_changed_token_count(self):
        text = "alpha beta gamma"
        new, _ = apply_mask(text, [{"word": "beta", "shap": 0.1}], "<mask>")
        self.assertEqual(count_changed_whitespace_tokens(text, new, "<mask>"), 1)


class TestSelectWords(unittest.TestCase):
    def setUp(self):
        self.items = [
            {"word": "a", "shap": 0.5},
            {"word": "b", "shap": -0.4},
            {"word": "c", "shap": 0.1},
            {"word": "d", "shap": -0.05},
            {"word": "e", "shap": 0.01},
        ]
        self.rng = random.Random(7)

    def test_pos(self):
        sel = select_words(self.items, "A_pos", 2, self.rng)
        self.assertEqual([w["word"] for w in sel], ["a", "c"])

    def test_neg(self):
        sel = select_words(self.items, "B_neg", 2, self.rng)
        self.assertEqual([w["word"] for w in sel], ["b", "d"])

    def test_abs(self):
        sel = select_words(self.items, "C_abs", 2, self.rng)
        self.assertEqual([w["word"] for w in sel], ["a", "b"])

    def test_lowabs(self):
        sel = select_words(self.items, "E_lowabs", 2, self.rng)
        self.assertEqual([w["word"] for w in sel], ["e", "d"])

    def test_random_size(self):
        sel = select_words(self.items, "D_random", 3, self.rng)
        self.assertEqual(len(sel), 3)

    def test_budget_not_exceed_vocab(self):
        sel = select_words(self.items, "C_abs", 100, self.rng)
        self.assertEqual(len(sel), 5)


class TestPunctAttached(unittest.TestCase):
    def test_match_word_with_period_in_attribs(self):
        text = "It went viral."
        # word_attribs sometimes attach punctuation
        span = locate_word_span(text, "viral.")
        self.assertIsNotNone(span)
        new, meta = apply_mask(text, [{"word": "viral.", "shap": 0.2}], "<mask>")
        self.assertEqual(meta["n_applied"], 1)
        self.assertIn("<mask>", new)


if __name__ == "__main__":
    unittest.main()
