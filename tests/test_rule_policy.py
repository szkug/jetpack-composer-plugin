"""Keep native activation/severity and scoring data on the same built-in policy."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/score'))
from rule_policy import load_policy


class RulePolicyTests(unittest.TestCase):
    def test_enabled_yaml_matches_entire_catalog_and_native_severities(self):
        catalog = json.loads((ROOT / 'references/score/catalog.json').read_text())
        text = (ROOT / 'scripts/verify/rules/detekt.yml').read_text()
        # This built-in YAML deliberately uses only plain two-level rule mappings.
        active = {}
        section = rule = None
        for line in text.splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            indent = len(line) - len(line.lstrip())
            key, _, value = line.strip().partition(':')
            if indent == 0:
                section, rule = key, None
            elif indent == 2 and not value.strip():
                rule = key
            elif indent == 4 and rule:
                row = active.setdefault(f'detekt.{section}.{rule}', {})
                if key in ('active', 'severity'):
                    row[key] = value.strip()
        enabled = {name: row for name, row in active.items() if row.get('active') == 'true'}
        expected = {name: row for name, row in catalog['rules'].items() if row['enabled']}
        self.assertEqual(set(enabled), set(expected))
        native = {'suggestion': 'info', 'warning': 'warning', 'error': 'error'}
        policy = load_policy()
        for name, row in expected.items():
            self.assertEqual(enabled[name]['severity'], native[row['severity']], name)
            self.assertEqual(row['weight'], policy['classes'][row['severity']]['deduction'])
        sha = hashlib.sha256(text.encode()).hexdigest()
        self.assertEqual(sha, catalog['default_config_sha256'])
        lock = json.loads((ROOT / 'scripts/verify/runtime/analyzers.lock.json').read_text())
        self.assertEqual(sha, lock['config_sha256'])

    def test_gate_cannot_be_weakened(self):
        for analyzer in ('lint', 'detekt'):
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/compose_quality.py'),
                                     analyzer, 'run', '--context', 'unused.json',
                                     '--fail-level', 'error'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('invalid choice', result.stderr)


if __name__ == '__main__':
    unittest.main()
