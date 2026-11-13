"""Independent Lint/detekt scores; unscored category labels, independent Lint detail/gate, no visual score."""
from copy import deepcopy
import re
from fractions import Fraction
from pathlib import Path

from score_common import digest, number, read_json, string_list, text_field
import diagnostics
from rule_policy import policy_digest

CATALOG = Path(__file__).resolve().parents[2] / 'references/score/catalog.json'
VERIFICATION = Path(__file__).resolve().parents[2] / 'references/verify'
COVERAGE = VERIFICATION / 'coverage.json'
BOUNDARIES = VERIFICATION / 'acceptance-boundaries.json'
ANALYZERS = ('android-lint', 'detekt')


def audit(manifest):
    catalog = read_json(CATALOG)
    if manifest['schema_version'] != 14 or manifest['catalog_sha256'] != digest(catalog):
        raise ValueError('v14 requires the frozen static catalog; historical visual scores cannot be imported')
    for field in ('protocol_id', 'frozen_at', 'scope', 'overlap_review'):
        text_field(manifest, field)
    if manifest['assessment_mode'] not in ('preregistered', 'retrospective'):
        raise ValueError('declare prior exposure')
    if any(key in manifest for key in ('quality_manifest', 'criteria', 'tool_acceptance')):
        raise ValueError('v14 does not accept manually scored quality predicates')
    if any(k in manifest for k in ('dimensions', 'excluded_dimensions', 'category_scores', 'category_budgets', 'weights', 'mean', 'total', 'total_score')):
        raise ValueError('v14 has only Lint/detekt scores; category budgets and combined totals are not supported')
    profiles = manifest['analyzer_profiles']
    if set(profiles) != set(ANALYZERS):
        raise ValueError('retain both tool evidence packets; Lint remains an independent gate')
    if len({p['base'] for p in profiles.values()}) != 1:
        raise ValueError('both tools require the same comparison base')
    if manifest['lint_policy_sha256'] != digest(read_json(diagnostics.POLICY)):
        raise ValueError('detail-score policy hash mismatch')
    if manifest.get('rule_policy_sha256') != policy_digest():
        raise ValueError('Freeze the shared built-in verification/scoring rule policy')
    required = {rule for rule, row in catalog['rules'].items() if row['enabled']}
    for analyzer, profile in profiles.items():
        for field in (*diagnostics.PROFILE_FIELDS, 'source_scope', 'coverage_note', 'rule_selection', 'collection_method', 'exclusions'):
            text_field(profile, field)
        if profile['scope'] != 'added-and-modified-lines' or profile.get('quality_owners', {}):
            raise ValueError('strict changed-line scope; no manual quality ownership in v14')
        rules = diagnostics.required_rules(analyzer, profile)
        diagnostics.rule_weights(analyzer, profile, catalog)
        if analyzer == 'detekt' and (profile['analysis_mode'] != 'full' or set(rules) != required):
            raise ValueError('v14 requires full analysis of the complete frozen Composer static profile')
        if analyzer == 'detekt':
            artifacts = profile['rule_artifacts_sha256']
            if not isinstance(artifacts, dict) or not artifacts or any(
                    not isinstance(v, str) or len(v) != 64 or any(c not in '0123456789abcdef' for c in v)
                    for v in artifacts.values()):
                raise ValueError('freeze exact rule artifact hashes before comparison')
    if manifest.get('acceptance_boundaries_sha256') != digest(read_json(BOUNDARIES)):
        raise ValueError('freeze the acceptance boundary and retirement ledger')
    audit_requirements(manifest, catalog)
    return {'schema_version': 14, 'manifest_sha256': digest(manifest), 'catalog_sha256': digest(catalog),
            'score_outputs': list(ANALYZERS), 'detekt_rules': len(required),
            'meaning': catalog['meaning'],
            'warnings': ['No visual or business acceptance score. A clean static profile is not proof of overall UI quality.']}


def audit_requirements(manifest, catalog):
    inventory = read_json(COVERAGE)
    if manifest.get('coverage_catalog_sha256') != digest(inventory):
        raise ValueError('freeze the complete requirement coverage catalog')
    all_rows = inventory['requirements']
    selected = all_rows
    scope = manifest.get('requirement_scope', {})
    if set(scope) != set(selected):
        raise ValueError('account for every selected static requirement; no silent omission')
    for key, row in selected.items():
        if row['kind'] != 'detector-contract' or row['coverage'] != 'static' or not row['rules']:
            raise ValueError('unimplemented/static coverage gaps cannot receive a score')
        atoms = row.get('atoms', [])
        static_rules = {a['rule'] for a in atoms if a['kind'] == 'static'}
        if static_rules != set(row['rules']) or len({a['id'] for a in atoms}) != len(atoms):
            raise ValueError('atomic predicates must exactly match rule links without duplicate IDs')
        if row['kind'] == 'semantic-obligation' and not any(a['kind'] != 'static' for a in atoms):
            raise ValueError('broad semantic requirement cannot lose its remaining obligation')
        declaration = scope[key]
        if set(declaration) != {'status', 'reason', 'evidence', 'authority'}:
            raise ValueError('requirement applicability needs status, reason, evidence and authority only')
        if declaration['status'] not in ('applicable', 'not_applicable'):
            raise ValueError('manual covered/pass/score overrides are not permitted')
        for field in ('reason', 'authority'):
            text_field(declaration, field)
        string_list(declaration['evidence'], 'requirement scope evidence')
        if row['kind'] == 'detector-contract' and declaration['status'] != 'applicable':
            raise ValueError('selected detector contracts cannot be removed using semantic exceptions')
        if not set(row['rules']) <= {r for r, policy in catalog['rules'].items() if policy['enabled']}:
            raise ValueError('coverage catalog references disabled/unavailable rules')
    return selected


def requirement_coverage(manifest, packets):
    rows = audit_requirements(manifest, read_json(CATALOG))
    executed = packets['detekt']['run']['rule_coverage']
    result = {}
    for key, row in rows.items():
        scope = manifest['requirement_scope'][key]
        if scope['status'] == 'not_applicable':
            status = 'not_applicable'
        elif row['coverage'] != 'static':
            status = row['coverage']
        elif all(executed[r]['status'] == 'executed' for r in row['rules']):
            status = 'covered'
        else:
            status = 'unverified'
        atoms = []
        for atom in row['atoms']:
            item = dict(atom)
            if scope['status'] == 'not_applicable':
                item['status'] = 'not_applicable'
            elif atom['kind'] != 'static':
                item['status'] = 'unverified'
            else:
                rule = atom['rule']
                item['status'] = 'checked' if executed[rule]['status'] == 'executed' else 'unverified'
                packet = packets['detekt']
                item['diagnostics'] = [f'matched:{i}' for i, issue in enumerate(packet['report']['matched'])
                                       if issue['id'] == rule and packet['reviews'][f'matched:{i}']['status'] == 'charge']
                item['observation'] = ('violations-reported' if item['diagnostics'] else 'no-confirmed-diagnostic')
            atoms.append(item)
        result[key] = {**row, 'atoms': atoms, 'status': status, 'applicability': scope}
    return result


def packet_with_default_reviews(packet):
    """Diagnostics score automatically; evidence-backed exceptions/duplicate groups may refine attribution."""
    result = deepcopy(packet)
    reviews = result.setdefault('reviews', {})
    for category in ('matched', 'unlocated'):
        for index, issue in enumerate(result['report'][category]):
            key = f'{category}:{index}'
            contract = None
            if issue['id'] == 'detekt.Composer.PositionalBooleanArguments':
                marker = re.match(r'\[composer-boolean-contract:([0-9a-f]{64})\]', issue['message'])
                if marker:
                    contract = 'boolean-callable-contract:' + marker.group(1)
            if key in reviews:
                if reviews[key]['status'] == 'covered':
                    raise ValueError('v14 has no manual quality points to cover a tool finding')
                if contract and reviews[key]['status'] == 'charge' and (
                        reviews[key].get('group') != contract or reviews[key].get('consequence_id') != contract):
                    raise ValueError('Boolean diagnostics must use the analyzer-proven callable counting unit')
                continue
            identity = contract or digest(issue)
            if issue['id'] in ('detekt.Composer.DroppedEventCallback', 'detekt.Composer.DroppedUiInput'):
                marker = re.match(r'\[composer-discarded:([0-9a-f]{64})\]', issue['message'])
                if marker:
                    identity = 'discarded-parameter:' + marker.group(1)
            reviews[key] = {'status': 'charge' if category == 'matched' else 'unknown',
                            'group': identity, 'consequence_id': identity,
                            'observation': issue['message'],
                            'evidence': [result['report_sha256'] + '/' + key],
                            'group_reason': ('Repeated Boolean naming findings on the same resolved callable share one defect group; all call sites remain repair obligations.' if contract else 'Identical diagnostics or the same analyzer-proven discarded leaf parameter form one defect; other merges need evidence.')}
    return result


def calculate(manifest, envelope, include_mean=False):
    if include_mean:
        raise ValueError('v14 has no mean or combined total; omit --mean and display Lint/detekt separately')
    audited = audit(manifest)
    if envelope['manifest_sha256'] != audited['manifest_sha256']:
        raise ValueError('manifest hash mismatch')
    for field in ('snapshot_id', 'evidence_set_id'):
        text_field(envelope, field)
    if envelope['review_mode'] not in ('self', 'independent', 'adjudicated'):
        raise ValueError('declare actual review mode')
    if any(key in envelope for key in ('quality', 'checks', 'dimension_scores', 'category_scores', 'category_budgets', 'mean', 'total', 'total_score', 'requirement_coverage', 'coverage_override')):
        raise ValueError('scores must come from tool diagnostics, not supplied manual grades')
    if set(envelope['analyzers']) != set(ANALYZERS):
        raise ValueError('both tool packets required')
    catalog = read_json(CATALOG)
    details, packets, missing = {}, {}, []
    for analyzer in ANALYZERS:
        profile = manifest['analyzer_profiles'][analyzer]
        packet = packet_with_default_reviews(envelope['analyzers'][analyzer])
        packets[analyzer] = packet
        run, report = packet['run'], packet['report']
        if digest(report) != packet['report_sha256']:
            raise ValueError('raw report hash mismatch')
        for field in ('analysis_mode', 'source_scope', 'coverage_note'):
            if run[field] != profile[field]:
                raise ValueError('execution scope differs from profile: ' + analyzer + '.' + field)
        if report.get('policy', {}).get('rulePolicySha256') != policy_digest():
            raise ValueError('Verification and scoring must use the same built-in rule policy')
        coverage = run['rule_coverage']
        required_rules = set(diagnostics.required_rules(analyzer, profile))
        if set(coverage) != required_rules:
            raise ValueError('every required rule requires explicit execution coverage')
        reported = {i['id'] for c in ('matched', 'unlocated', 'excluded') for i in report[c]}
        if not reported <= required_rules:
            raise ValueError('report contains undeclared rules')
        for rule, proof in coverage.items():
            string_list(proof['evidence'], 'rule coverage evidence')
            if proof['status'] not in ('executed', 'unavailable', 'suppressed', 'unverified'):
                raise ValueError('invalid rule coverage status')
            if proof['status'] != 'executed':
                missing.append(analyzer + ':' + rule)
        if analyzer == 'detekt':
            policy = report['policy']
            standalone = policy.get('integration') == 'standalone-cli'
            if standalone:
                if (policy.get('contextVerified') is not True or not policy.get('contextProvenance')
                        or not policy.get('contextFile', {}).get('sha256')
                        or not policy.get('classpath') or not policy.get('sourceInputs')
                        or not policy.get('analyzerLockSha256') or not policy.get('jvmTarget')
                        or not policy.get('native', {}).get('executable')):
                    raise ValueError('standalone detekt receipt lacks frozen compilation-context inputs')
                enabled = {r['id'] for r in report.get('rule_inventory', [])
                           if r.get('configuration', {}).get('enabled') is True}
                if not set(profile['required_rules']) <= enabled:
                    raise ValueError('standalone CLI did not report the complete enabled detekt rule profile')
            if (report.get('analyzer') != 'detekt' or report.get('analysis_mode') != 'full'
                    or policy.get('version') != catalog['detekt_version']
                    or policy.get('composeRulesVersion') != catalog['compose_rules_version']
                    or policy.get('composerRulesVersion') != catalog['composer_rules_version']
                    or policy.get('mode') != 'full'
                    or policy.get('module') != run['module'] or policy.get('variant') != run['variant']
                    or policy.get('autoCorrect') is not False
                    or (not standalone and policy.get('originalProjectEvaluated') is not True)):
                raise ValueError('detekt receipt lacks pinned rule execution and compilation context')
            native_severity = {'error': 'Error', 'warning': 'Warning', 'suggestion': 'Information'}
            for bucket in ('matched', 'excluded', 'unlocated'):
                for issue in report[bucket]:
                    if issue['severity'] != native_severity[catalog['rules'][issue['id']]['severity']]:
                        raise ValueError('detekt native severity differs from built-in policy: ' + issue['id'])
            names = {p['name'] for p in policy.get('pluginClasspath', []) if p.get('sha256')}
            if not {'composer-quality-rules.jar', 'detekt-' + catalog['compose_rules_version'] + '.jar'} <= names:
                raise ValueError('missing custom/maintained rule artifact receipts')
            actual_artifacts = {p['name']: p['sha256'] for p in policy['pluginClasspath']}
            if actual_artifacts != profile['rule_artifacts_sha256']:
                raise ValueError('rule artifacts differ from the frozen profile')
            if [p['sha256'] for p in policy['configFiles']] != [catalog['default_config_sha256']]:
                raise ValueError('v14 scoring requires the exact bundled rule configuration; project activation/severity overrides are not accepted')
            if digest([p['sha256'] for p in policy['configFiles']]) != profile['configuration_sha256']:
                raise ValueError('executed detekt configuration differs from the frozen ordered hashes')
        detail = diagnostics.score_packet(profile, packet, envelope['snapshot_id'])
        if analyzer == 'android-lint':
            inventory = profile['rule_inventory']
            policy = report.get('policy', {})
            if policy.get('ruleInventory') != inventory:
                detail['missing_checks'].append('lint.complete-inventory-unverified')
            configs = policy.get('configFiles', [])
            if not configs or digest([p.get('sha256') for p in configs]) != profile['configuration_sha256']:
                detail['missing_checks'].append('lint.configuration-unverified')
            if policy.get('allRegisteredRulesExecuted') is not True:
                detail['missing_checks'].append('lint.all-rule-execution-unverified')
            if run.get('rule_severities') != profile['rule_severities']:
                detail['missing_checks'].append('lint.rule-severities-unverified')
            for bucket in ('matched', 'excluded', 'unlocated'):
                for issue in report[bucket]:
                    if issue['severity'] != profile['rule_severities'][issue['id']]:
                        detail['missing_checks'].append('lint.severity-drift:' + issue['id'])
        missing.extend(analyzer + ':' + k for k in detail['missing_checks'])
        if any(k.startswith(analyzer + ':') for k in missing):
            detail['missing_checks'] = sorted(set(detail['missing_checks']) | {
                k.split(':', 1)[1] for k in missing if k.startswith(analyzer + ':')})
            if detail['gate'] != 'failed':
                detail['gate'] = 'incomplete'
        detail.update(diagnostics.deduction_rule_score(
            diagnostics.rule_weights(analyzer, profile, catalog), detail, coverage))
        for rule, row in detail['rule_results'].items():
            row['severity'] = (profile['rule_severities'][rule] if analyzer == 'android-lint'
                               else catalog['rules'][rule]['severity'])
        if detail['repair_required']:
            detail['gate'] = 'failed'
        details[analyzer] = {**detail, 'id': analyzer, 'name': 'Lint severity deduction score' if analyzer == 'android-lint' else 'detekt severity deduction score'}

    groups = {}
    rows = details['detekt']['diagnostics']
    for key, row in details['detekt']['groups'].items():
        rules = {rows[ref]['issue']['id'] for ref in row['diagnostics']}
        # A representative owner only labels the defect; every failing rule is scored above.
        owner = min(rules, key=lambda rule: (-catalog['rules'][rule]['weight'], catalog['rules'][rule]['ownership_priority'], rule))
        policy = catalog['rules'][owner]
        groups[key] = {**row, 'primary_rule': owner, 'rules': sorted(rules),
                       'category': policy['category'], 'severity': policy['severity'], 'rationale': policy['rationale'],
                       'occurrence_count': len(row['diagnostics']),
                       'counting_unit': policy.get('defect_counting_unit', 'distinct diagnostic or evidenced semantic owner')}
    coverage = requirement_coverage(manifest, packets)
    labels = []
    for label in catalog['categories']:
        owned = {k: g for k, g in groups.items() if g['category'] == label['id']}
        labels.append({**label, 'finding_count': len(owned), 'group_ids': sorted(owned),
                       'rules': [r for r in manifest['analyzer_profiles']['detekt']['required_rules']
                                 if catalog['rules'][r]['category'] == label['id']]})
    missing.extend('requirement:' + key for key, row in coverage.items() if row['status'] != 'covered')
    detekt_detail = details['detekt']
    detekt_detail.update(name='detekt severity deduction score', groups=groups)
    quality_gate = ('failed' if any(d['gate'] == 'failed' for d in details.values())
                    else 'incomplete' if missing else 'passed')
    result = {'schema_version': 14, 'manifest_sha256': digest(manifest), 'decision_sha256': digest(envelope),
              'snapshot_id': envelope['snapshot_id'], 'evidence_set_id': envelope['evidence_set_id'],
              'review_mode': envelope['review_mode'], 'audit': audited,
              'meaning': catalog['meaning'], 'score_scope': 'frozen-static-rule-compliance',
              'external_acceptance': {'scored': False, 'status': 'not-assessed', 'ledger': read_json(BOUNDARIES)},
              'requirement_coverage': coverage, 'quality_gate': quality_gate, 'categories': labels, 'analyzer_scores': details,
              'deduplicated_groups': groups,
              'analyzer_gates': {a: d['gate'] for a, d in details.items()},
              'publication_status': 'withheld' if missing else 'complete', 'missing_checks': sorted(set(missing)),
              'acceptance': 'Static gates only; business/build/runtime acceptance is reported separately.',
              'score_policy': 'Independent deduction scores: suggestion=1, warning=2, error=3; each failing rule is charged once; warnings/errors require repair, suggestions require a contextual decision; no combined tool score.'}
    return result


def compare(manifest, envelopes, include_mean=False, agreement=False):
    if len(envelopes) < 2:
        raise ValueError('at least two records required')
    results = [calculate(manifest, e, include_mean) for e in envelopes]
    if agreement:
        for field in ('snapshot_id', 'evidence_set_id'):
            if len({e[field] for e in envelopes}) != 1:
                raise ValueError('agreement requires identical frozen source/evidence')
        for analyzer in ANALYZERS:
            if len({digest({'report': e['analyzers'][analyzer]['report'],
                            'coverage': e['analyzers'][analyzer]['run']['rule_coverage']}) for e in envelopes}) != 1:
                raise ValueError('agreement requires identical raw reports and coverage')
    elif len({e['snapshot_id'] for e in envelopes}) != len(envelopes):
        raise ValueError('distinct snapshots required; use --agreement to review the same evidence')
    def review_changes(left, right):
        left_reviews = packet_with_default_reviews(left)['reviews']
        right_reviews = packet_with_default_reviews(right)['reviews']
        return [key for key, value in left_reviews.items() if value != right_reviews.get(key)]
    return {'mode': 'repeat-review agreement' if agreement else 'candidate comparison', 'results': results,
            'publication_status': 'withheld' if any(r['missing_checks'] for r in results) else 'complete',
            'differences': [{'snapshot_id': r['snapshot_id'],
                             'review_differences': {a: review_changes(envelopes[0]['analyzers'][a], envelopes[index]['analyzers'][a])
                                                    for a in ANALYZERS} if agreement else None,
                             'analyzer_differences': {analyzer: number(Fraction(r['analyzer_scores'][analyzer]['score']) - Fraction(results[0]['analyzer_scores'][analyzer]['score']))
                                 if r['analyzer_scores'][analyzer]['score'] is not None and results[0]['analyzer_scores'][analyzer]['score'] is not None else None
                                 for analyzer in ANALYZERS}} for index, r in enumerate(results[1:], 1)],
            'interpretation': 'Static compliance protocol v14; external acceptance is unscored. Only compare the two analyzer scores separately; no average or category grades.'}
