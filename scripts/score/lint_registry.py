"""Parse complete native Lint discovery output; shared by collection and scoring."""
import re


def parse_inventory(listing, descriptions):
    ids = re.findall(r'^"([A-Za-z][A-Za-z0-9_]*)":', listing, re.M)
    rows = re.findall(r'^([A-Za-z][A-Za-z0-9_]*)\n-+\nSummary:.*?^Severity: (\w+)\s*$',
                      descriptions, re.M | re.S)
    severities = dict(rows)
    if not ids or len(ids) != len(set(ids)) or len(rows) != len(severities) or set(ids) != set(severities):
        raise ValueError('Native Lint --list and --show inventories differ or are empty/duplicated')
    if any(s not in ('Fatal', 'Error', 'Warning', 'Information', 'Informational', 'Hint') for s in severities.values()):
        raise ValueError('Unsupported native default severity; cannot silently drop a rule')
    return dict(sorted(severities.items()))

