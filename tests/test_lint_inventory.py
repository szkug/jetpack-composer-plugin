"""Native discovery must retain non-Compose IDs and fail closed on partial output."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/verify'))
from lint_inventory import parse_inventory


class LintInventoryTests(unittest.TestCase):
    def test_all_ids_and_default_disabled_rules_are_retained(self):
        listing = '"NewApi": API\n"ComposeExample": Compose\n"StopShip": disabled by default\n'
        descriptions = ''.join(f'{rule}\n-------\nSummary: example\n\nSeverity: {severity}\nNOTE: disabled by default\n\n'
                               for rule, severity in [('NewApi', 'Error'), ('ComposeExample', 'Warning'), ('StopShip', 'Fatal')])
        self.assertEqual(parse_inventory(listing, descriptions),
                         {'NewApi': 'Error', 'ComposeExample': 'Warning', 'StopShip': 'Fatal'})

    def test_partial_duplicate_or_unknown_inventory_is_rejected(self):
        listing = '"NewApi": API\n'
        description = 'NewApi\n------\nSummary: API\nSeverity: Error\n'
        for ids, rows in [('', ''), (listing, ''), (listing * 2, description),
                          (listing, description * 2), (listing, description.replace('Error', 'Ignore'))]:
            with self.assertRaises(ValueError):
                parse_inventory(ids, rows)
