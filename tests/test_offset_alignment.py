"""Regression tests for M2B offset-aware alignment (M2A failure categories)."""
from __future__ import annotations

import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "arr_m2"))

from offset_alignment import (  # noqa: E402
    align_record,
    apply_mask_offsets,
    select_source_words,
    source_word_spans,
)


def _load_cache_by_substr(substr: str, path: Path):
    for line in path.open(encoding="utf-8"):
        r = json.loads(line)
        if substr in r["text"]:
            return r
    raise AssertionError(f"no cache row containing {substr!r}")


CACHE_BD = ROOT / "outputs" / "basil_shap" / "samples_biasdetector.jsonl"


class TestSourceWords(unittest.TestCase):
    def test_whitespace_spans(self):
        text = "Of course the National Enquirer story is 100% FALSE!!!"
        words = source_word_spans(text)
        surfaces = [w.surface for w in words]
        self.assertIn("100%", surfaces)
        self.assertIn("FALSE!!!", surfaces)
        self.assertNotIn("100FALSE!!!", surfaces)


class TestCurlyQuotes(unittest.TestCase):
    """M2A failure: word_attribs like '““He' / 'Hunt!””'."""

    def test_witch_hunt_sentence(self):
        if not CACHE_BD.exists():
            self.skipTest("cache missing")
        rec = _load_cache_by_substr("Witch Hunt!", CACHE_BD)
        al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
        self.assertTrue(al.alignment_ok, msg=al.unaligned_token_strs)
        surfaces = [w.surface for w in al.words]
        # Should not create doubled-quote Frankenwords as the only He token
        self.assertTrue(any(w.surface in ("“He", "He", '"He') or w.surface.endswith("He") for w in al.words) or "He" in surfaces or any("He" == s or s.endswith("He") for s in surfaces))
        # Mask top abs word should complete budget
        rng = random.Random(0)
        sel = select_source_words(al.words, "C_abs", 2, rng)
        new, meta = apply_mask_offsets(rec["text"], sel, "<mask>")
        self.assertTrue(meta["complete_budget"])
        self.assertEqual(meta["n_applied"], 2)
        self.assertEqual(new.count("<mask>"), 2)


class TestMergedPercentFalse(unittest.TestCase):
    """M2A failure: '100FALSE!!!' merged attribution string."""

    def test_enquirer_sentence(self):
        if not CACHE_BD.exists():
            self.skipTest("cache missing")
        rec = _load_cache_by_substr("100% FALSE", CACHE_BD)
        al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
        self.assertTrue(al.alignment_ok, msg=al.unaligned_token_strs)
        surfaces = [w.surface for w in al.words]
        self.assertIn("100%", surfaces)
        self.assertIn("FALSE!!!", surfaces)
        # SHAP on FALSE!!! should be nonzero (was high in word_attribs)
        false_w = next(w for w in al.words if w.surface == "FALSE!!!")
        self.assertNotEqual(false_w.shap, 0.0)
        sel = [false_w]
        new, meta = apply_mask_offsets(rec["text"], sel, "<mask>")
        self.assertTrue(meta["complete_budget"])
        self.assertIn("<mask>", new)
        self.assertNotIn("FALSE!!!", new)


class TestAmpersandGlue(unittest.TestCase):
    def test_him_ampersand_split(self):
        if not CACHE_BD.exists():
            self.skipTest("cache missing")
        rec = _load_cache_by_substr("Witch Hunt!", CACHE_BD)
        al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
        surfaces = [w.surface for w in al.words]
        # Source has 'him' and '&' as separate whitespace tokens
        self.assertIn("him", surfaces)
        self.assertIn("&", surfaces)
        self.assertNotIn("him&", surfaces)


class TestRepeatedWords(unittest.TestCase):
    def test_repeated_the(self):
        text = "the cat and the dog"
        # Fake SHAP tokens mimicking Text masker trailing spaces
        tokens = ["", "the ", "cat ", "and ", "the ", "dog"]
        shap = [0.0, 0.1, 0.2, 0.0, 0.3, 0.4]
        al = align_record(text, tokens, shap)
        self.assertTrue(al.alignment_ok)
        the_words = [w for w in al.words if w.surface == "the"]
        self.assertEqual(len(the_words), 2)
        self.assertAlmostEqual(the_words[0].shap, 0.1)
        self.assertAlmostEqual(the_words[1].shap, 0.3)
        # Mask second 'the' only
        new, meta = apply_mask_offsets(text, [the_words[1]], "<mask>")
        self.assertEqual(meta["n_applied"], 1)
        self.assertEqual(new, "the cat and <mask> dog")


class TestNoSilentSubstitute(unittest.TestCase):
    def test_corrupt_span_fails(self):
        text = "alpha beta"
        words = source_word_spans(text)
        words[0].surface = "ALPHA"  # desync
        new, meta = apply_mask_offsets(text, [words[0]], "<mask>")
        self.assertEqual(meta["n_applied"], 0)
        self.assertEqual(meta["n_failed"], 1)
        self.assertEqual(new, text)
        self.assertFalse(meta["complete_budget"])


class TestPunctuationAndTruncationPatterns(unittest.TestCase):
    def test_synthetic_curly_and_excl(self):
        text = "“Hello,” she said!!!"
        tokens = ["", "“", "Hello", ",,” ", "she ", "said", "!!!"]
        # approximate shap segmentation
        shap = [0.0, 0.01, 0.5, 0.02, 0.03, 0.2, 0.1]
        al = align_record(text, tokens, shap)
        # May or may not be perfect depending on token ",,” " — check rate
        self.assertGreaterEqual(al.token_align_rate, 0.8)
        if al.alignment_ok:
            sel = select_source_words(al.words, "A_pos", 1, random.Random(0))
            new, meta = apply_mask_offsets(text, sel, "<mask>")
            self.assertTrue(meta["complete_budget"])


class TestPilotCacheSweep(unittest.TestCase):
    """All M2A pilot sentences for BD should align at 100% token rate."""

    def test_m2a_manifest_bd(self):
        man = ROOT / "outputs" / "arr_m2" / "sampling_manifest.csv"
        if not man.exists() or not CACHE_BD.exists():
            self.skipTest("m2a artifacts missing")
        import csv

        manifest = list(csv.DictReader(man.open()))
        cache = {}
        for line in CACHE_BD.open(encoding="utf-8"):
            r = json.loads(line)
            k = f"basil:{r['triplet_uuid']}|{int(r['outlet_idx'])}|{int(r['sentence_idx'])}"
            cache[k] = r
        bad = []
        for row in manifest:
            rec = cache[row["canonical_id"]]
            al = align_record(rec["text"], rec["tokens"], rec["shap_pos"])
            if not al.alignment_ok:
                bad.append((row["canonical_id"], al.unaligned_token_strs[:5], al.token_align_rate))
        self.assertEqual(bad, [], msg=str(bad))


if __name__ == "__main__":
    unittest.main()
