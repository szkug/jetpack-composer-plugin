#!/usr/bin/env python3
"""Native detekt CLI with bundled Compose rules and changed-line report filtering."""
import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urljoin, urlparse

from incremental_lint import changed_lines, git, snapshot, write_json

VERSION = '2.0.0-alpha.6'
COMPOSE_RULES_VERSION = '0.6.8'
COMPOSER_RULES_VERSION = '1.4.1'
HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def input_digest(path):
    path = Path(path)
    if path.is_file():
        return sha(path)
    if not path.is_dir():
        raise ValueError('Missing classpath input: ' + str(path))
    digest = hashlib.sha256()
    for file in sorted(p for p in path.rglob('*') if p.is_file()):
        digest.update(file.relative_to(path).as_posix().encode() + b'\0')
        digest.update(bytes.fromhex(sha(file)))
    return digest.hexdigest()


def location_name(artifact, run, root):
    uri = artifact.get('uri')
    if uri is None and 'index' in artifact:
        artifact = run['artifacts'][artifact['index']]['location']
        uri = artifact.get('uri', '')
    uri = uri or ''
    base_id = artifact.get('uriBaseId')
    seen = set()
    while base_id:
        if base_id in seen:
            raise ValueError('Cyclic SARIF URI base')
        seen.add(base_id)
        base = run.get('originalUriBaseIds', {}).get(base_id)
        if not base and base_id == '%SRCROOT%':
            base = {'uri': root.as_uri() + '/'}
        if not base:
            raise ValueError('Unknown SARIF URI base: ' + base_id)
        uri = urljoin(base.get('uri', ''), uri)
        base_id = base.get('uriBaseId')
    parsed = urlparse(uri)
    if parsed.scheme not in ('', 'file') or parsed.netloc not in ('', 'localhost'):
        raise ValueError('Unsupported source URI: ' + uri)
    if not uri:
        return ''
    file = Path(unquote(parsed.path))
    file = file if file.is_absolute() else root / file
    try:
        return file.resolve().relative_to(root).as_posix()
    except ValueError:
        return str(file.resolve())


def check(out, cli_exit):
    from standalone_scan import validate_run
    manifest, receipt, errors = validate_run(out, cli_exit)
    root = Path(manifest['root'])
    report = out / 'detekt.sarif'
    matched, excluded, unlocated, rule_inventory = [], [], [], []
    if not errors:
        sarif = json.loads(report.read_text())
        if sarif.get('version') != '2.1.0' or not sarif.get('runs'):
            raise ValueError('Not a nonempty SARIF 2.1.0 report')
        for run in sarif['runs']:
            if run['tool']['driver']['name'].lower() != 'detekt':
                raise ValueError('Unexpected analyzer in report')
            for invocation in run.get('invocations', []):
                if invocation.get('executionSuccessful') is False:
                    errors.append('Analyzer reports incomplete execution')
                for note in invocation.get('toolExecutionNotifications', []):
                    if note.get('level') == 'error':
                        errors.append('Analyzer notification: ' + note['message']['text'])
            rules = {rule['id']: rule for rule in run['tool']['driver'].get('rules', [])}
            rule_inventory.extend({'id': rule['id'], 'configuration': rule.get('defaultConfiguration', {})}
                                  for rule in rules.values())
            for issue in run.get('results', []):
                rule = issue['ruleId']
                level = issue.get('level', rules.get(rule, {}).get('defaultConfiguration', {}).get('level', 'warning'))
                severity = {'error': 'Error', 'warning': 'Warning', 'note': 'Information', 'none': 'Ignore'}[level]
                item = {'id': rule, 'analyzer': 'detekt', 'severity': severity,
                        'message': issue['message']['text'], 'locations': []}
                for loc in issue.get('locations', []):
                    physical = loc.get('physicalLocation', {})
                    name = location_name(physical.get('artifactLocation', {}), run, root)
                    region = physical.get('region', {})
                    # Declaration-wide endLine does NOT turn unchanged headers into changed findings.
                    item['locations'].append({'file': name, 'line': int(region.get('startLine', 0)),
                                              'column': int(region.get('startColumn', 0)),
                                              'end_line': int(region.get('endLine', 0)),
                                              'end_column': int(region.get('endColumn', 0))})
                hit = any(any(a <= loc['line'] <= b for a, b in manifest['changes'].get(loc['file'], []))
                          for loc in item['locations'])
                bucket = matched if hit else excluded if any(loc['line'] for loc in item['locations']) else unlocated
                bucket.append(item)
    blocked = [i for i in matched if i['severity'] in ('Error', 'Fatal') or
               (manifest['fail_level'] == 'warning' and i['severity'] == 'Warning')]
    status = 2 if errors else 1 if blocked else 0
    result = {'analyzer': 'detekt', 'exit_code': status, 'base': manifest['base'],
              'scope': 'added-and-modified-lines', 'errors': errors,
              'matched': matched, 'excluded': excluded, 'unlocated': unlocated,
              'policy': receipt, 'profile': manifest['profile'], 'analysis_mode': manifest['analysis_mode'],
              'coverage_note': manifest['coverage_note'], 'rule_inventory': rule_inventory,
              'blocking_count': len(blocked)}
    write_json(out / 'result.json', result)
    print(json.dumps({'exit_code': status, 'matched': len(matched), 'excluded': len(excluded),
                      'unlocated': len(unlocated), 'errors': errors, 'report': str(out / 'result.json')}))
    return status


def main():
    from standalone_scan import main as run_native
    return run_native('detekt')


if __name__ == '__main__':
    try:sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print('Native detekt execution failed: ' + str(error), file=sys.stderr);sys.exit(2)
