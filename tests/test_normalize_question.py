"""Tests for the typo normalizer."""

from __future__ import annotations

import pytest

from app.chatbot.normalize_question import normalize_question


class TestNormalize:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            ("compitior brands", "competitor brands"),
            ("Compitior Brands", "competitor brands"),  # map values are always lowercase
            ("who are my compitiors", "who are my competitors"),
            ("revanue last week", "revenue last week"),
            ("categary mix", "category mix"),
            ("brnad rankings", "brand rankings"),
            ("prodcut count", "product count"),
            ("marekt share", "market share"),
            ("canabis sales", "cannabis sales"),
            ("flwer top", "flower top"),
            ("preroll list", "pre-roll list"),
            ("edibel prices", "edible prices"),
            ("concntrate trend", "concentrate trend"),
            ("cartrige under 25", "cartridge under 25"),
            ("prce avg", "price avg"),
            ("qty by brand", "quantity by brand"),
            ("helo there", "hello there"),
            ("thanx", "thanks"),
            ("oders pending", "orders pending"),
            ("invntory low", "inventory low"),
        ],
    )
    def test_known_mappings(self, raw, expected):
        assert normalize_question(raw) == expected

    def test_preserves_punctuation_and_spaces(self):
        assert normalize_question("  Compitior  brands!?") == "  competitor  brands!?"

    def test_leaves_unknown_tokens_untouched(self):
        s = "show me Berry Fizz strain in vermont"
        assert normalize_question(s) == s

    def test_empty_string(self):
        assert normalize_question("") == ""

    def test_no_letters(self):
        assert normalize_question("   ?!,.  ") == "   ?!,.  "

    def test_does_not_touch_substrings_inside_other_words(self):
        # "tyrant" contains "ty" — must NOT be rewritten to "thanksrant".
        assert normalize_question("tyrant") == "tyrant"

    def test_idempotent(self):
        once = normalize_question("compitior brnad revanue")
        twice = normalize_question(once)
        assert once == twice
