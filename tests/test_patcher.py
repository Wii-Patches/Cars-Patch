import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))

import features
from regions import REGIONS


class TestCarsPatcher(unittest.TestCase):
    def test_regions(self):
        self.assertEqual(len(REGIONS), 12)
        self.assertEqual({m['game'] for m in REGIONS.values()}, {'cars', 'mater', 'ror'})

    def test_features(self):
        self.assertEqual(features.FEATURES, ('cc', 'gc', 'pitstop', 'fov'))

    def test_cars_only_features(self):
        for region, meta in REGIONS.items():
            for name in ('pitstop', 'fov'):
                self.assertEqual(features.available(name, region), meta['game'] == 'cars', (name, region))

    def test_gc_pulls_in_cc(self):
        self.assertEqual(features.closure(['gc']), ['cc', 'gc'])
        self.assertEqual(features.closure(['cc']), ['cc'])

    def test_prebuilt_features(self):
        for region in REGIONS:
            for name in features.FEATURES:
                if not features.applies(name, region):
                    continue
                feat = features.load(name, region)
                self.assertTrue(feat.ops)
                self.assertTrue(feat.gecko_lines())

    def test_every_release_is_verified(self):
        # built from each release's own retail main.dol (tools/gen_prebuilt.py)
        for region in REGIONS:
            for name in features.FEATURES:
                if features.available(name, region):
                    self.assertTrue(features.load(name, region).verified, (name, region))


if __name__ == '__main__':
    unittest.main()
