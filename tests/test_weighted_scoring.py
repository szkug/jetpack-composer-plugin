"""Regression checks for rule weighting, shared policy and evidence gates."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/score'))
import calculate
import diagnostics
import engine
from score_common import digest


class WeightedScoringTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / 'references/score/example-manifest.json').read_text())
        self.evidence = json.loads((ROOT / 'references/score/example-decisions.json').read_text())

    def score(self):
        self.evidence['manifest_sha256'] = digest(self.manifest)
        for packet in self.evidence['analyzers'].values():
            packet['report_sha256'] = digest(packet['report'])
        return calculate.calculate(self.manifest, self.evidence)

    def sync_synthetic_inventory(self):
        inventory = self.manifest['analyzer_profiles']['android-lint']['rule_inventory']
        inventory['discovery_output'] = {
            'list': ''.join(f'"{rule}": Synthetic rule\n' for rule in inventory['rules']),
            'show': ''.join(f'{rule}\n-------\nSummary: Synthetic rule\nSeverity: {severity}\n\n'
                            for rule, severity in inventory['rules'].items())}
        inventory['discovery'] = {key: hashlib.sha256(value.encode()).hexdigest()
                                  for key, value in inventory['discovery_output'].items()}
        self.evidence['analyzers']['android-lint']['report']['policy']['ruleInventory'] = copy.deepcopy(inventory)

    def test_three_classes_and_floor(self):
        for weights, expected in [({'s': 1, 'w': 2, 'e': 3}, '94'),
                                  ({str(i): 3 for i in range(40)}, '0')]:
            detail = {'diagnostics': {rule: {'status': 'charge', 'issue': {'id': rule}}
                                      for rule in weights}, 'missing_checks': [], 'groups': {}}
            row = diagnostics.deduction_rule_score(weights, detail,
                {rule: {'status': 'executed'} for rule in weights})
            self.assertEqual(row['score'], expected)
            self.assertEqual(row['raw_deductions'], sum(weights.values()))
            self.assertEqual(row['applied_deductions'], min(100, sum(weights.values())))

    def test_clean_and_all_failing_boundaries(self):
        for packet in self.evidence['analyzers'].values():
            packet['report']['matched'] = []
            packet['report']['exit_code'] = 0
        result = self.score()
        self.assertEqual(result['quality_gate'], 'passed')
        for row in result['analyzer_scores'].values():
            self.assertEqual(row['score'], '100')
            self.assertEqual(row['applied_deductions'], 0)
        lint = self.evidence['analyzers']['android-lint']
        lint['report']['matched'] = [{'id': 'ComposeModifierWithoutDefault', 'severity': 'Error',
                                     'message': 'Violation', 'locations': []}]
        self.assertEqual(self.score()['analyzer_scores']['android-lint']['score'], '97')

    def test_repeated_rule_across_locations_charged_once(self):
        before = self.score()['analyzer_scores']['detekt']
        packet = self.evidence['analyzers']['detekt']
        for i in range(100):
            issue = copy.deepcopy(packet['report']['matched'][0])
            issue['locations'][0]['file'] = f'src/Other{i}.kt'
            packet['report']['matched'].append(issue)
        after = self.score()['analyzer_scores']['detekt']
        self.assertEqual(after['score'], before['score'])
        self.assertEqual(after['raw_deductions'], before['raw_deductions'])
        self.assertEqual(after['failed_rule_count'], 2)
        self.assertEqual(after['finding_count'], 102)
        self.assertEqual(after['defect_count'], 102)

    def test_same_defect_does_not_hide_another_failing_rule(self):
        packet = self.evidence['analyzers']['detekt']
        packet['reviews'] = {f'matched:{i}': {'status': 'charge', 'group': 'shared',
            'consequence_id': 'shared', 'observation': 'Evidence-backed same underlying defect',
            'group_reason': 'Shared defect only, not a shared scoring rule', 'evidence': ['synthetic source']}
            for i in range(2)}
        row = self.score()['analyzer_scores']['detekt']
        self.assertEqual(row['defect_count'], 1)
        self.assertEqual(row['failed_rule_count'], 2)
        self.assertEqual(row['raw_deductions'], 4)

    def test_exception_does_not_fail_rule(self):
        packet = self.evidence['analyzers']['android-lint']
        packet['reviews'] = {'matched:0': {'status': 'exception', 'exception_kind': 'false-positive',
            'authority': 'synthetic detector/source adjudication', 'alternative_evidence': 'synthetic proof',
            'observation': 'Confirmed false positive', 'evidence': ['synthetic source']}}
        row = self.score()['analyzer_scores']['android-lint']
        self.assertEqual((row['score'], row['failed_rule_count'], row['finding_count']), ('100', 0, 0))
        self.assertEqual(row['gate'], 'failed')  # original native gate remains visible

    def test_exception_does_not_hide_other_violation_of_same_rule(self):
        packet = self.evidence['analyzers']['android-lint']
        packet['report']['matched'].append(copy.deepcopy(packet['report']['matched'][0]))
        packet['report']['matched'][1]['locations'][0]['line'] += 1
        packet['reviews'] = {'matched:0': {'status': 'exception', 'exception_kind': 'false-positive',
            'authority': 'synthetic adjudication', 'alternative_evidence': 'synthetic proof',
            'observation': 'One false positive only', 'evidence': ['synthetic source']}}
        row = self.score()['analyzer_scores']['android-lint']
        self.assertEqual((row['failed_rule_count'], row['raw_deductions'], row['finding_count']), (1, 3, 1))

    def test_severity_receipt_mismatch_withholds_score(self):
        self.evidence['analyzers']['android-lint']['run']['rule_severities'] = {
            'ComposeModifierWithoutDefault': 'Warning'}
        self.assertIsNone(self.score()['analyzer_scores']['android-lint']['score'])

    def test_unknown_withholds_only_affected_tool(self):
        self.evidence['analyzers']['android-lint']['reviews'] = {'matched:0': {
            'status': 'unknown', 'observation': 'Applicability unresolved', 'evidence': ['source pending']}}
        result = self.score()
        lint = result['analyzer_scores']['android-lint']
        self.assertIsNone(lint['score'])
        self.assertIsNone(lint['applied_deductions'])
        self.assertEqual(lint['total_rule_count'], 1)
        self.assertIsNotNone(result['analyzer_scores']['detekt']['score'])
        self.assertEqual(result['publication_status'], 'withheld')

    def test_unexecuted_rule_keeps_inventory(self):
        expected = self.score()['analyzer_scores']['detekt']['total_rule_count']
        packet = self.evidence['analyzers']['detekt']
        rule = 'detekt.Compose.ComposableNaming'
        packet['run']['rule_coverage'][rule]['status'] = 'unverified'
        row = self.score()['analyzer_scores']['detekt']
        self.assertEqual(row['total_rule_count'], expected)
        self.assertIsNone(row['score'])
        self.assertIsNone(row['passed_rule_count'])
        self.assertEqual(row['rule_results'][rule]['status'], 'unverified')

    def test_missing_lint_severity_receipt_withholds_score(self):
        del self.evidence['analyzers']['android-lint']['run']['rule_severities']
        result = self.score()
        self.assertIsNone(result['analyzer_scores']['android-lint']['score'])
        self.assertEqual(result['publication_status'], 'withheld')

    def test_severity_escalation_cannot_reduce_weight(self):
        rule = 'ComposeModifierWithoutDefault'
        self.manifest['analyzer_profiles']['android-lint']['rule_severities'][rule] = 'Warning'
        self.evidence['analyzers']['android-lint']['run']['rule_severities'][rule] = 'Warning'
        self.manifest['analyzer_profiles']['android-lint']['rule_inventory']['rules'][rule] = 'Warning'
        self.sync_synthetic_inventory()
        row = self.score()['analyzer_scores']['android-lint']
        self.assertIsNone(row['score'])
        self.assertTrue(any('severity-drift' in key for key in row['missing_checks']))

    def test_blocking_finding_is_not_canceled_by_high_score(self):
        for packet in self.evidence['analyzers'].values():
            packet['report']['matched'] = []
            packet['report']['exit_code'] = 0
        packet = self.evidence['analyzers']['detekt']
        packet['report']['matched'] = [{'id': 'detekt.Composer.StateWriteInComposition',
            'severity': 'Error', 'message': 'State mutation', 'locations': []}]
        result = self.score()
        self.assertEqual(result['analyzer_scores']['detekt']['applied_deductions'], 3)
        self.assertGreater(float(result['analyzer_scores']['detekt']['score']), 95)
        self.assertEqual(result['quality_gate'], 'failed')

    def test_lint_error_blocks_even_when_native_exit_is_zero(self):
        self.evidence['analyzers']['android-lint']['report']['exit_code'] = 0
        result = self.score()
        self.assertEqual(result['analyzer_scores']['android-lint']['gate'], 'failed')
        self.assertEqual(result['quality_gate'], 'failed')

    def test_bad_or_empty_inventory_is_rejected(self):
        profile = self.manifest['analyzer_profiles']['android-lint']
        for severity in ('Ignore', 'unknown'):
            profile['rule_severities']['ComposeModifierWithoutDefault'] = severity
            with self.assertRaises(ValueError):
                self.score()
        profile['rule_severities'] = {}
        with self.assertRaises(ValueError):
            self.score()
        profile['selected_rules'] = []
        with self.assertRaises(ValueError):
            self.score()

    def test_missing_inventory_provenance_is_rejected(self):
        self.manifest['analyzer_profiles']['android-lint']['rule_severity_evidence'] = []
        with self.assertRaises(ValueError):
            self.score()

    def add_non_compose_rule(self):
        profile = self.manifest['analyzer_profiles']['android-lint']
        packet = self.evidence['analyzers']['android-lint']
        profile['rule_inventory']['rules']['NewApi'] = 'Error'
        profile['rule_severities']['NewApi'] = 'Error'
        packet['run']['rule_severities']['NewApi'] = 'Error'
        packet['run']['rule_coverage']['NewApi'] = {'status': 'executed', 'evidence': ['synthetic complete scan']}
        self.sync_synthetic_inventory()

    def test_unreported_non_compose_rule_is_in_inventory(self):
        self.add_non_compose_rule()
        row = self.score()['analyzer_scores']['android-lint']
        self.assertEqual((row['total_rule_count'], row['raw_deductions'], row['score']), (2, 3, '97'))

    def test_lint_selected_rules_cannot_shrink_inventory(self):
        self.add_non_compose_rule()
        self.manifest['analyzer_profiles']['android-lint']['selected_rules'] = ['ComposeModifierWithoutDefault']
        with self.assertRaisesRegex(ValueError, 'selected_rules is forbidden'):
            self.score()

    def test_dropped_rule_severity_or_coverage_is_rejected(self):
        self.add_non_compose_rule()
        profile = self.manifest['analyzer_profiles']['android-lint']
        del profile['rule_severities']['NewApi']
        with self.assertRaises(ValueError):
            self.score()
        profile['rule_severities']['NewApi'] = 'Error'
        del self.evidence['analyzers']['android-lint']['run']['rule_coverage']['NewApi']
        with self.assertRaises(ValueError):
            self.score()

    def test_missing_provider_or_rule_receipt_withholds_full_inventory(self):
        self.add_non_compose_rule()
        policy = self.evidence['analyzers']['android-lint']['report']['policy']
        for field in ('providers', 'rules'):
            old = policy['ruleInventory'][field]
            policy['ruleInventory'][field] = {}
            row = self.score()['analyzer_scores']['android-lint']
            self.assertIsNone(row['score'])
            self.assertEqual(row['total_rule_count'], 2)
            policy['ruleInventory'][field] = old
        del policy['allRegisteredRulesExecuted']
        self.assertIsNone(self.score()['analyzer_scores']['android-lint']['score'])

    def test_filtering_frozen_map_cannot_hide_native_rule(self):
        self.add_non_compose_rule()
        profile = self.manifest['analyzer_profiles']['android-lint']
        del profile['rule_inventory']['rules']['NewApi']
        del profile['rule_severities']['NewApi']
        with self.assertRaisesRegex(ValueError, 'complete native inventory'):
            self.score()

    def test_configuration_drift_withholds_score(self):
        self.evidence['analyzers']['android-lint']['report']['policy']['configFiles'] = []
        self.assertIsNone(self.score()['analyzer_scores']['android-lint']['score'])

    def test_lint_missing_rule_keeps_full_inventory(self):
        self.add_non_compose_rule()
        self.evidence['analyzers']['android-lint']['run']['rule_coverage']['NewApi']['status'] = 'unavailable'
        row = self.score()['analyzer_scores']['android-lint']
        self.assertEqual(row['total_rule_count'], 2)
        self.assertIsNone(row['score'])

    def test_v12_cannot_be_silently_reinterpreted(self):
        self.manifest['schema_version'] = 12
        with self.assertRaisesRegex(ValueError, 'schema_version 14'):
            self.score()

    def test_compare_uses_same_inventory_for_candidates(self):
        first = copy.deepcopy(self.evidence)
        second = copy.deepcopy(first)
        second['snapshot_id'] = 'second-source'
        second['evidence_set_id'] = 'second-evidence'
        for packet in second['analyzers'].values():
            packet['run']['snapshot_id'] = second['snapshot_id']
            packet['report']['matched'] = []
            packet['report']['exit_code'] = 0
            packet['report_sha256'] = digest(packet['report'])
        result = engine.compare(self.manifest, [first, second])
        for analyzer in engine.ANALYZERS:
            left, right = [row['analyzer_scores'][analyzer] for row in result['results']]
            self.assertEqual(left['total_rule_count'], right['total_rule_count'])
            self.assertEqual(right['score'], '100')

    def test_policy_drift_rejected(self):
        self.manifest['rule_policy_sha256'] = '0' * 64
        with self.assertRaises(ValueError):
            self.score()

    def test_scan_policy_drift_rejected(self):
        for analyzer in engine.ANALYZERS:
            original = self.evidence['analyzers'][analyzer]['report']['policy']['rulePolicySha256']
            self.evidence['analyzers'][analyzer]['report']['policy']['rulePolicySha256'] = '0' * 64
            with self.assertRaises(ValueError):
                self.score()
            self.evidence['analyzers'][analyzer]['report']['policy']['rulePolicySha256'] = original

    def test_detekt_severity_cannot_drift(self):
        self.evidence['analyzers']['detekt']['report']['matched'][0]['severity'] = 'Information'
        with self.assertRaisesRegex(ValueError, 'native severity differs'):
            self.score()

    def test_lint_lower_severity_also_withholds_score(self):
        self.evidence['analyzers']['android-lint']['report']['matched'][0]['severity'] = 'Information'
        self.assertIsNone(self.score()['analyzer_scores']['android-lint']['score'])

    def test_suggestions_deduct_without_blocking(self):
        for packet in self.evidence['analyzers'].values():
            packet['report']['matched'] = []
            packet['report']['exit_code'] = 0
        packet = self.evidence['analyzers']['detekt']
        packet['report']['matched'] = [{'id': 'detekt.Compose.MissingNonRestartableComposable',
            'severity': 'Information', 'message': 'Suggestion', 'locations': []}]
        row = self.score()['analyzer_scores']['detekt']
        self.assertEqual(row['score'], '99')
        self.assertEqual(row['gate'], 'passed')
        self.assertFalse(row['repair_required'])
        self.assertEqual(row['severity_counts'], {'suggestion': 1, 'warning': 0, 'error': 0})

    def test_warning_blocks_even_with_zero_exit(self):
        self.evidence['analyzers']['detekt']['report']['exit_code'] = 0
        row = self.score()['analyzer_scores']['detekt']
        self.assertEqual(row['score'], '96')
        self.assertEqual(row['gate'], 'failed')

    def test_v13_is_rejected(self):
        self.manifest['schema_version'] = 13
        with self.assertRaisesRegex(ValueError, 'schema_version 14'):
            self.score()


if __name__ == '__main__':
    unittest.main()
