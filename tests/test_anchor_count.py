"""Portable mathematical regressions for the exact printed PAM-3 count."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from anchor_count_proof import verify_count

class AnchorCountTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = json.loads((ROOT / 'inputs/anchor-pam3.json').read_text())
        result = json.loads((ROOT / 'results/anchor-pam3.json').read_text())
        cls.mappings = {tuple(int(word, 2) for word in row['mapping']) for row in result['records']}
        cls.proof = verify_count(cls.spec, cls.mappings)

    def test_exact_count_has_two_complete_isometry_orbits(self):
        self.assertEqual(self.proof['exact_count'], 96)
        self.assertEqual(self.proof['cube_cycle_count_factors'], [8, 3, 4])
        self.assertEqual(self.proof['input_isometry_orbit_sizes'], [48, 48])

    def test_unpruned_replay_covers_every_injection(self):
        self.assertEqual(self.proof['unpruned_injections_checked'], 362880)
        self.assertTrue(self.proof['all_mapping_sets_equal'])

    def test_truncating_to_source_reported_72_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'mapping sets differ'):
            verify_count(self.spec, set(sorted(self.mappings)[:72]))

    def test_source_quotation_is_not_rewritten_to_the_computed_count(self):
        changed = deepcopy(self.spec)
        changed['source_text_reported_pairwise_count'] = 96
        with self.assertRaisesRegex(ValueError, 'source quotation changed'):
            verify_count(changed, self.mappings)

if __name__ == '__main__':
    unittest.main()
