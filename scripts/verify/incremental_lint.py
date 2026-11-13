#!/usr/bin/env python3
"""Android Lint CLI with bundled rules and Git changed-line report filtering."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def git(root, *args):
    result = subprocess.run(['git', '--literal-pathspecs', '-C', str(root), *args], capture_output=True)
    if result.returncode:
        raise ValueError('Git command failed: ' + result.stderr.decode(errors='replace')[:1000])
    return result.stdout


def paths(raw):
    return [os.fsdecode(x) for x in raw.split(b'\0') if x]


def snapshot(root, base):
    digest = hashlib.sha256(git(root, 'diff', '--binary', '--no-ext-diff', '--no-textconv', base, '--'))
    for name in sorted(paths(git(root, 'ls-files', '--others', '--exclude-standard', '-z'))):
        file = root / name
        digest.update(os.fsencode(name) + b'\0')
        digest.update(file.read_bytes() if file.is_file() else b'<not-file>')
    return digest.hexdigest()


def changed_lines(root, base):
    records = paths(git(root, 'diff', '--name-status', '-z', '--find-renames', base, '--'))
    changed = {}
    i = 0
    while i < len(records):
        status, name = records[i:i + 2]
        i += 2
        selected = [name]
        if status.startswith(('R', 'C')):
            name = records[i]
            i += 1
            selected.append(name)
        if status == 'D':
            continue
        patch = git(root, 'diff', '--no-ext-diff', '--no-textconv', '--no-color',
                    '--unified=0', '--find-renames', base, '--', *selected).decode(errors='replace')
        ranges = []
        for match in re.finditer(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@', patch, re.M):
            start, count = int(match[1]), int(match[2] or '1')
            if count:
                ranges.append([start, start + count - 1])
        changed[name] = ranges
    for name in paths(git(root, 'ls-files', '--others', '--exclude-standard', '-z')):
        file = root / name
        if file.is_file():
            count = len(file.read_bytes().splitlines())
            changed[name] = [[1, count]] if count else []
    return changed


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def check(out, cli_exit):
    from standalone_scan import validate_run
    manifest, receipt, errors = validate_run(out, cli_exit)
    root = Path(manifest['root'])
    report = out / 'lint.xml'
    matched, excluded, unlocated = [], [], []
    if not errors:
        tree = ET.parse(report).getroot()
        if tree.tag != 'issues':
            raise ValueError('Not an Android lint XML report')
        for issue in tree.findall('issue'):
            item = {k: issue.get(k, '') for k in ('id', 'severity', 'message')}
            item['locations'] = []
            for loc in issue.findall('location'):
                file = Path(loc.get('file', ''))
                if not file.is_absolute():
                    file = Path(receipt['projectDir']) / file
                try:
                    name = file.resolve().relative_to(root).as_posix()
                except ValueError:
                    name = str(file.resolve())
                line = int(loc.get('line', '0'))
                item['locations'].append({'file': name, 'line': line, 'column': int(loc.get('column', '0'))})
            if item['id'] in {'LintError', 'ParserError'}:
                errors.append(item['id'] + ': ' + item['message'])
            # Any explicitly reported location on a changed line is relevant.
            hit = any(any(start <= loc['line'] <= end
                          for start, end in manifest['changes'].get(loc['file'], []))
                      for loc in item['locations'])
            if hit:
                matched.append(item)
            elif not item['locations'] or not any(loc['line'] for loc in item['locations']):
                unlocated.append(item)
            else:
                excluded.append(item)
    levels = {'ignore': -1, 'hint': 0, 'information': 0, 'informational': 0,
              'warning': 1, 'error': 2, 'fatal': 3}
    threshold = 1 if manifest['fail_level'] == 'warning' else 2
    blocked = [item for item in matched if levels.get(item['severity'].lower(), 2) >= threshold]
    status = 2 if errors else (1 if blocked else 0)
    inventory = receipt.get('ruleInventory')
    if inventory:
        # Prepared command, provider hashes and override policy are validated above.
        receipt['allRegisteredRulesExecuted'] = not errors
    result = {'exit_code': status, 'base': manifest['base'], 'scope': 'added-and-modified-lines',
              'errors': errors, 'matched': matched, 'excluded': excluded, 'unlocated': unlocated,
              'policy': receipt, 'blocking_count': len(blocked)}
    write_json(out / 'result.json', result)
    print(json.dumps({'exit_code': status, 'matched': len(matched), 'excluded': len(excluded),
                      'unlocated': len(unlocated), 'blocking': len(blocked), 'errors': errors,
                      'report': str(out / 'result.json')}, ensure_ascii=False))
    return status


def main():
    from standalone_scan import main as run_native
    return run_native('lint')


if __name__ == '__main__':
    try:sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, ET.ParseError) as error:
        print('Native lint execution failed: ' + str(error), file=sys.stderr);sys.exit(2)
