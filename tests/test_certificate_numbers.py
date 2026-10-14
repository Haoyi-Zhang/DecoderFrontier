"""Owned finite certificate numeric-domain checks, excluding the POSIX CLI."""
import ast
from copy import deepcopy
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / 'src' / 'fixed_codebook_check.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
names = {'need', 'require_exact_numbers', 'validate_certificate_numbers'}
selected = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
if {node.name for node in selected} != names:
    raise RuntimeError('numeric-domain production functions missing')
namespace = {'math': math}
exec(compile(ast.Module(body=selected, type_ignores=[]), str(source), 'exec'), namespace)
validate = namespace['validate_certificate_numbers']


class CertificateNumberTests(unittest.TestCase):
    def test_integer_science_and_finite_timing_metadata(self):
        record = {'case': {'k': 2, 'encoder': ['01', '10']}, 'frontier': [[1,20]],
                  'cpu_seconds': 0.125, 'wall_seconds': 0.25}
        original = deepcopy(record)
        validate(record)
        self.assertEqual(record, original)

    def test_semantic_bool_and_float_aliases_are_rejected(self):
        for value in (True, False, 1.0, 0.0):
            for record in ({'case': {'k': value}}, {'frontier': [[value,20]]},
                           {'encoder_plane': {'packing': [[0,value]]}}):
                with self.subTest(value=value, record=record):
                    with self.assertRaises(ValueError):
                        validate(record)

    def test_invalid_timing_is_not_a_scientific_integer(self):
        for key in ('cpu_seconds','wall_seconds'):
            for value in (True, -1, float('nan'), float('inf'), '0.1'):
                with self.subTest(key=key,value=value):
                    with self.assertRaises(ValueError):
                        validate({key:value})


if __name__ == '__main__':
    unittest.main()
