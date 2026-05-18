#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/unit/test_mrerp_cache.py

Unit tests for services/erp/_master_data_cache.py (P1-B Phase 1).
"""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from services.erp._master_data_cache import TTLCache   # noqa: E402


class BasicTests(unittest.TestCase):

    def test_get_missing_returns_none(self):
        c = TTLCache()
        self.assertIsNone(c.get("nope"))
        self.assertEqual(c.misses, 1)
        self.assertEqual(c.hits, 0)

    def test_set_then_get(self):
        c = TTLCache()
        c.set("k", "v")
        self.assertEqual(c.get("k"), "v")
        self.assertEqual(c.hits, 1)

    def test_replace_existing(self):
        c = TTLCache()
        c.set("k", 1)
        c.set("k", 2)
        self.assertEqual(c.get("k"), 2)

    def test_invalidate(self):
        c = TTLCache()
        c.set("k", "v")
        self.assertTrue(c.invalidate("k"))
        self.assertIsNone(c.get("k"))
        self.assertFalse(c.invalidate("k"))   # already gone

    def test_clear(self):
        c = TTLCache()
        c.set("a", 1); c.set("b", 2)
        c.clear()
        self.assertEqual(len(c), 0)
        self.assertEqual(c.hits, 0)
        self.assertEqual(c.misses, 0)


class LRUTests(unittest.TestCase):

    def test_eviction_when_full(self):
        c = TTLCache(max_size=2, ttl_seconds=30)
        c.set("a", 1)
        c.set("b", 2)
        c.set("c", 3)   # evicts "a" (oldest)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)
        self.assertEqual(len(c), 2)

    def test_get_promotes_recency(self):
        c = TTLCache(max_size=2, ttl_seconds=30)
        c.set("a", 1)
        c.set("b", 2)
        c.get("a")       # touches "a"; now "b" is oldest
        c.set("c", 3)    # should evict "b", not "a"
        self.assertEqual(c.get("a"), 1)
        self.assertIsNone(c.get("b"))


class TTLTests(unittest.TestCase):

    def test_expiry_drops_entry(self):
        # 0.05s TTL, sleep 0.1s, expect miss.
        c = TTLCache(max_size=8, ttl_seconds=0.05)
        c.set("k", "v")
        self.assertEqual(c.get("k"), "v")
        time.sleep(0.1)
        self.assertIsNone(c.get("k"))
        self.assertEqual(len(c), 0)   # expired entry was purged on get


class ValidationTests(unittest.TestCase):

    def test_bad_max_size(self):
        with self.assertRaises(ValueError):
            TTLCache(max_size=0)

    def test_bad_ttl(self):
        with self.assertRaises(ValueError):
            TTLCache(ttl_seconds=0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
