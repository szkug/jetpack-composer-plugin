"""Validate diagnostics and calculate shared-policy distinct-rule deductions."""
import hashlib
from lint_registry import parse_inventory
from rule_policy import load_policy, policy_digest
from collections import Counter
from pathlib import Path

from score_common import digest, read_json, string_list, text_field

POLICY = Path(__file__).resolve().parents[2] / 'references/score/lint-policy.json'
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
        if severity not in {*policy['severity_weights'], *policy['unscored_severities']}:
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
            item = groups.setdefault(group, {'consequence_id': consequence, 'diagnostics': []})
            if item['consequence_id'] != consequence:
                raise ValueError('one defect group cannot hide distinct consequences')
            item['diagnostics'].append(key)
        identity = digest(issue)
        disposition = (action, decision.get('group'), decision.get('criterion'))
        if identity in identities and identities[identity] != disposition:
            raise ValueError('identical diagnostic has contradictory dispositions')
        identities[identity] = disposition
        rows[key] = {'issue': issue, **decision}
    if len({g['consequence_id'] for g in groups.values()}) != len(groups):
        raise ValueError('one lint consequence cannot be charged in multiple groups')
    blocking = any(row['status'] == 'charge' and row['issue']['severity'] in ('Fatal', 'Error', 'Warning')
                   for row in rows.values())
    return {'id': 'android-lint', 'name': policy['name'],
            'groups': groups, 'diagnostics': rows, 'missing_checks': sorted(set(missing)),
            'matched_count': len(report['matched']), 'unlocated_count': len(report['unlocated']),
            'excluded_count': len(report['excluded']), 'scope': report['scope'],
            'raw_severity_counts': {category: dict(Counter(i['severity'] for i in report[category]))
                                    for category in ('matched', 'unlocated', 'excluded')},
            'tool_exit_code': report['exit_code'],
            'gate': 'failed' if report['exit_code'] == 1 or blocking else 'incomplete' if missing else 'passed',
            'meaning': policy['meaning']}


def required_rules(analyzer, profile):
    if analyzer == 'detekt':
        return string_list(profile['required_rules'], 'complete detekt rule IDs')
    if 'selected_rules' in profile:
        raise ValueError('Lint selected_rules is forbidden; use the complete native rule_inventory')
    inventory = profile['rule_inventory']
    if inventory.get('rule_policy_sha256') != policy_digest():
        raise ValueError('Lint inventory differs from the shared built-in rule policy')
    if inventory.get('schema_version') != 1 or inventory.get('mode') != 'all-registered':
        raise ValueError('Lint requires the complete all-registered native inventory')
    for field in ('providers', 'discovery'):
        values = inventory.get(field)
        if not isinstance(values, dict) or not values or any(
                not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                for v in values.values()):
            raise ValueError('Lint inventory requires exact provider/discovery hashes')
    if set(inventory['discovery']) != {'list', 'show'}:
        raise ValueError('Lint requires both native registry discovery receipts')
    output = inventory.get('discovery_output', {})
    if set(output) != {'list', 'show'} or any(
            not isinstance(value, str) or hashlib.sha256(value.encode()).hexdigest() != inventory['discovery'][key]
            for key, value in output.items()):
        raise ValueError('Lint native discovery output is missing or changed')
    native_rules = parse_inventory(output['list'], output['show'])
    rules = inventory.get('rules')
    if not isinstance(rules, dict):
        raise ValueError('Lint inventory rules must contain every native ID and severity')
    if rules != native_rules or rules != profile['rule_severities']:
        raise ValueError('Lint severity map must exactly match the complete native inventory')
    return string_list(list(rules), 'complete native Lint rule IDs')


def rule_weights(analyzer, profile, catalog):
    """Resolve weights from the frozen rule inventory, including rules with no findings."""
    rules = required_rules(analyzer, profile)
    builtin = load_policy()
    if analyzer == 'detekt':
        if catalog['severity_policy'] != {name: {'weight': row['deduction'], 'must_fix': row['must_fix'],
                                              'gate': 'failed' if row['must_fix'] else 'advisory'}
                                           for name, row in builtin['classes'].items()}:
            raise ValueError('detekt severity policy differs from built-in rule policy')
        weights = {rule: catalog['rules'][rule]['weight'] for rule in rules}
        for rule in rules:
            row = catalog['rules'][rule]
            if not row['enabled'] or weights[rule] != catalog['severity_policy'][row['severity']]['weight']:
                raise ValueError('detekt rule weight differs from severity policy: ' + rule)
    else:
        severities = profile['rule_severities']
        if not isinstance(severities, dict) or set(severities) != set(rules):
            raise ValueError('freeze an effective Lint severity for every required rule')
        string_list(profile['rule_severity_evidence'], 'Lint inventory/config severity evidence')
        policy = read_json(POLICY)
        expected_weights = {severity: builtin['classes'][kind]['deduction']
                            for severity, kind in builtin['native_severity_classes'].items()}
        if policy['severity_weights'] != expected_weights:
            raise ValueError('Lint deductions differ from built-in rule policy')
        if any(severity not in policy['severity_weights'] for severity in severities.values()):
            raise ValueError('required Lint rules must have enabled, scored severities')
        weights = {rule: policy['severity_weights'][severities[rule]] for rule in rules}
    if any(type(weight) is not int or weight not in (1, 2, 3) for weight in weights.values()):
        raise ValueError('rule deductions must be suggestion=1, warning=2, error=3')
    return weights


def deduction_rule_score(weights, detail, coverage):
    """Charge each confirmed failing rule once, without losing occurrence/defect evidence."""
    failures = {rule: [] for rule in weights}
    for ref, row in detail['diagnostics'].items():
        if row['status'] == 'charge':
            failures[row['issue']['id']].append(ref)
    failed = {rule for rule, refs in failures.items() if refs}
    policy = load_policy()
    initial = policy['score']['initial']
    lost = sum(weights[rule] for rule in failed)
    complete = not detail['missing_checks']
    return {
        'score': str(max(policy['score']['floor'], initial - lost)) if complete else None,
        'starting_score': initial,
        'raw_deductions': lost,
        'applied_deductions': min(initial, lost) if complete else None,
        'total_rule_count': len(weights),
        'passed_rule_count': len(weights) - len(failed) if complete else None,
        'failed_rule_count': len(failed),
        'severity_counts': {name: sum(weights[rule] == row['deduction'] for rule in failed)
                            for name, row in policy['classes'].items()},
        'deductions_by_severity': {name: sum(weights[rule] for rule in failed
                                               if weights[rule] == row['deduction'])
                                   for name, row in policy['classes'].items()},
        'repair_required': any(weights[rule] >= 2 for rule in failed),
        'finding_count': sum(len(refs) for refs in failures.values()),
        'defect_count': len(detail['groups']),
        'rule_results': {rule: {
            'deduction': weight,
            'classification': next(name for name, row in policy['classes'].items() if row['deduction'] == weight),
            'must_fix': weight >= 2,
            'status': 'failed' if rule in failed else 'passed' if complete else 'unverified',
            'execution_status': coverage[rule]['status'],
            'finding_count': len(failures[rule]), 'diagnostics': failures[rule],
        } for rule, weight in sorted(weights.items())},
        'formula': policy['score']['formula'],
        'meaning': 'Distinct-rule deduction score out of 100; deductions remain observed lower bounds when evidence is incomplete.',
    }
