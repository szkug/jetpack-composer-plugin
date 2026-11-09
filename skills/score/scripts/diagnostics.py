"""Validate a current analyzer packet and group evidence-backed diagnostic deductions."""
from collections import Counter
from pathlib import Path

from score_common import digest, read_json, string_list, text_field

POLICY = Path(__file__).resolve().parents[1] / 'references/lint-policy.json'
PROFILE_FIELDS = ('base', 'module', 'variant', 'toolchain', 'configuration_sha256')


def score_packet(profile, packet, snapshot_id):
    policy = read_json(POLICY)
    report, run, reviews = (packet[k] for k in ('report', 'run', 'reviews'))
    if packet['report_sha256'] != digest(report):
        raise ValueError('lint report hash mismatch')
    if run['snapshot_id'] != snapshot_id:
        raise ValueError('lint and quality must evaluate the same frozen source')
    for field in PROFILE_FIELDS:
        if run[field] != profile[field]:
            if field == 'base' and run[field] in profile.get('base_equivalents', {}):
                continue
            raise ValueError('lint run differs from frozen profile: ' + field)
    string_list(run['evidence'], 'lint run evidence')
    if report['scope'] != policy['scope'] or report['base'] != run['base']:
        raise ValueError('lint diff scope/base differs')
    missing = []
    for field in ('receipt_verified', 'source_unchanged', 'execution_complete'):
        if not isinstance(run[field], bool):
            raise ValueError('lint run verification flags must be boolean')
        if not run[field]:
            missing.append('lint.' + field)
    if type(report['exit_code']) is not int or report['exit_code'] not in (0, 1):
        missing.append('lint.execution')
    if not isinstance(report['errors'], list):
        raise ValueError('lint errors must be a list')
    if report['errors']:
        missing.append('lint.engine-errors')
    incidents = {}
    for category in ('matched', 'unlocated', 'excluded'):
        if not isinstance(report[category], list):
            raise ValueError('lint category must be a list: ' + category)
        if category != 'excluded':
            incidents.update({f'{category}:{i}': item for i, item in enumerate(report[category])})
    if not isinstance(reviews, dict) or set(reviews) != set(incidents):
        raise ValueError('review every matched and unlocated diagnostic exactly once')
    groups, rows, identities = {}, {}, {}
    for key, issue in incidents.items():
        text_field(issue, 'id')
        severity = text_field(issue, 'severity')
        if severity not in policy['deductions']:
            raise ValueError('unsupported lint severity: ' + severity)
        decision = reviews[key]
        action = decision['status']
        if action not in ('charge', 'exception', 'out-of-scope', 'unknown'):
            raise ValueError('invalid lint disposition: ' + key)
        text_field(decision, 'observation')
        string_list(decision['evidence'], 'lint decision evidence')
        if key.startswith('unlocated:') and action not in ('out-of-scope', 'unknown'):
            raise ValueError('unlocated finding needs scope adjudication or a corrected scan')
        if action == 'unknown':
            missing.append('lint.' + key)
        elif action in ('exception', 'out-of-scope'):
            text_field(decision, 'authority')
            if action == 'exception':
                if decision['exception_kind'] not in ('E1', 'E2', 'E3', 'E4', 'false-positive'):
                    raise ValueError('use a documented exception or proven detector false positive')
                text_field(decision, 'alternative_evidence')
        else:
            group = text_field(decision, 'group')
            text_field(decision, 'group_reason')
            consequence = text_field(decision, 'consequence_id')
            item = groups.setdefault(group, {'consequence_id': consequence, 'deduction': 0, 'diagnostics': []})
            if item['consequence_id'] != consequence:
                raise ValueError('one deduction group cannot hide distinct consequences')
            item['deduction'] = max(item['deduction'], policy['deductions'][severity])
            item['diagnostics'].append(key)
        identity = digest(issue)
        disposition = (action, decision.get('group'), decision.get('criterion'))
        if identity in identities and identities[identity] != disposition:
            raise ValueError('identical diagnostic has contradictory dispositions')
        identities[identity] = disposition
        rows[key] = {'issue': issue, **decision}
    if len({g['consequence_id'] for g in groups.values()}) != len(groups):
        raise ValueError('one lint consequence cannot be charged in multiple groups')
    deducted = sum(g['deduction'] for g in groups.values())
    score = max(0, 100 - deducted) if not missing else None
    return {'id': 'android-lint', 'name': policy['name'], 'score': str(score) if score is not None else None,
            'raw_deductions': deducted, 'applied_deductions': min(100, deducted) if score is not None else None,
            'groups': groups, 'diagnostics': rows, 'missing_checks': sorted(set(missing)),
            'matched_count': len(report['matched']), 'unlocated_count': len(report['unlocated']),
            'excluded_count': len(report['excluded']), 'scope': report['scope'],
            'raw_severity_counts': {category: dict(Counter(i['severity'] for i in report[category]))
                                    for category in ('matched', 'unlocated', 'excluded')},
            'tool_exit_code': report['exit_code'],
            'gate': 'failed' if report['exit_code'] == 1 else 'incomplete' if missing else 'passed',
            'meaning': policy['meaning']}
