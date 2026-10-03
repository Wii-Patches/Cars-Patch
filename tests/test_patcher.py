import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', 'tools')
sys.path.insert(0, TOOLS)

import features
import patcher
from regions import ALL_REGIONS, GAMES

class TestCarsPatcher(unittest.TestCase):
    def test_regions_loaded(self):
        self.assertEqual(len(ALL_REGIONS), 12)
        self.assertEqual(len(GAMES), 3)

    def test_prebuilt_features(self):
        for reg_id, meta in ALL_REGIONS.items():
            for f in meta['features']:
                self.assertTrue(features.available(f, reg_id), f"Missing {f} for {reg_id}")
                feat = features.load(f, reg_id)
                self.assertTrue(len(feat.ops) > 0)

    def test_gecko_generation(self):
        for reg_id, meta in ALL_REGIONS.items():
            for f in meta['features']:
                feat = features.load(f, reg_id)
                lines = feat.gecko_lines()
                self.assertTrue(len(lines) > 0)

if __name__ == '__main__':
    unittest.main()
