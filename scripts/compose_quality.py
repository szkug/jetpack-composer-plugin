#!/usr/bin/env python3
"""Global Compose static-quality CLI; no project dependency installation or automatic checks."""
from collections import Counter
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/verify'))
from cli_bundle import APP_ID, describe, verify

ROUTES = {
    'lint': 'scripts/verify/incremental_lint.py',
    'detekt': 'scripts/verify/incremental_detekt.py',
    'score': 'scripts/score/calculate.py',
    'compare': 'scripts/score/compare.py',
    'chart': 'scripts/score/chart.py',
}


def metadata():
    if (ROOT / 'cli-manifest.json').is_file():
        return verify(ROOT)
    if (ROOT / 'SKILL.md').is_file():
        return describe(ROOT)
    raise ValueError('CLI bundle manifest is missing; reinstall from the trusted package')


def identity(record):
    return {k: record[k] for k in ('application_id', 'command', 'version', 'protocol',
                                 'bundle_sha256', 'enabled_detekt_rules', 'detekt_version',
                                 'compose_rules_version', 'composer_rules_version')}


def doctor(args, record):
    project = Path(args.project).resolve() if args.project else None
    java = Path(os.environ['JAVA_HOME']) / 'bin/java' if os.environ.get('JAVA_HOME') else shutil.which('java')
    checks = {'python_3_9_plus': sys.version_info >= (3, 9),
              'bundle_integrity': True, 'git_available': shutil.which('git') is not None,
              'java_available': bool(java and Path(java).is_file())}
    if args.android:
        sdk = os.environ.get('ANDROID_HOME') or os.environ.get('ANDROID_SDK_ROOT')
        if not sdk and project and (project / 'local.properties').is_file():
            for line in (project / 'local.properties').read_text().splitlines():
                if line.strip().startswith('sdk.dir='):
                    sdk = line.strip().split('=', 1)[1].replace('\\:', ':').replace('\\ ', ' ')
                    break
        checks['android_sdk_available'] = bool(sdk and (Path(sdk) / 'platforms').is_dir())
    if project:
        result = subprocess.run(['git', '-C', str(project), 'rev-parse', '--is-inside-work-tree'],
                                capture_output=True, text=True) if checks['git_available'] else None
        checks['git_worktree_available'] = result is not None and result.returncode == 0
    from ensure_analyzers import ensure
    for tool in ['lint', 'detekt']:
        status = ensure(tool, check=True)
        checks[tool + '_cli_available'] = status['status'] != 'missing-or-incompatible'
    result = {'cli': identity(record), 'checks': checks, 'ready': all(checks.values()),
              'note': 'Read-only prerequisite check, not a build or analysis. Native CLI availability is checked without a build. Full analysis needs an explicit compilation-context file.'}
    print(json.dumps(result, indent=2) if args.json else '\n'.join(
        [f'compose-quality {record["version"]}'] + [f'{name}: {"ok" if value else "missing"}' for name, value in checks.items()] + [result['note']]))
    return 0 if result['ready'] else 2


def main():
    if sys.version_info < (3, 9):
        print('compose-quality needs Python 3.9 or newer.', file=sys.stderr)
        return 2
    # Preserve the mature analyzers/parsers and exact exit statuses, including native prepare/check execution.
    if len(sys.argv) > 1 and sys.argv[1] in ROUTES:
        metadata()
        command, rest = sys.argv[1], sys.argv[2:]
        if command in ('lint', 'detekt') and (not rest or rest[0].startswith('-') and rest[0] not in ('-h', '--help')):
            rest = ['run'] + rest
        return subprocess.call([sys.executable, str(ROOT / ROUTES[command]), *rest])
    parser = argparse.ArgumentParser(prog='compose-quality', description=__doc__,
        epilog='Analysis: lint/detekt [run|prepare|check] ARGS. Scoring: score MANIFEST EVIDENCE, compare MANIFEST EVIDENCE... . Use COMMAND --help for its arguments. No combined score.')
    parser.add_argument('--version', action='store_true')
    parser.add_argument('--json', action='store_true', help='Machine-readable version output')
    commands = parser.add_subparsers(dest='command')
    p = commands.add_parser('doctor', help='Inspect native CLI prerequisites without running analysis')
    p.add_argument('--project')
    p.add_argument('--android', action='store_true', help='Also check ANDROID_HOME/ANDROID_SDK_ROOT or project sdk.dir')
    p.add_argument('--json', action='store_true')
    p = commands.add_parser('rules', help='Show bundled, pinned rule inventory and scoring policy')
    p.add_argument('--json', action='store_true')
    for name in ROUTES:
        commands.add_parser(name, add_help=False, help='Run ' + name + '; see compose-quality ' + name + ' --help')
    args = parser.parse_args()
    if not args.version and not args.command:
        parser.print_help()
        return 0
    record = metadata()
    if args.version:
        print(json.dumps(identity(record)) if args.json else 'compose-quality ' + record['version'])
        return 0
    if args.command == 'doctor':
        return doctor(args, record)
    catalog = json.loads((ROOT / 'references/score/catalog.json').read_text())
    rules = {name: row for name, row in catalog['rules'].items() if row['enabled']}
    result = {'cli': identity(record), 'lint': {'providers': ['Android/Compose official Lint', 'Slack Compose Lint'],
        'slack_version': '1.6.1', 'scoring': 'max(0, 100 - distinct failing rule deductions); suggestion=1, warning=2, error=3'},
        'detekt': {'rules': rules, 'scoring': 'max(0, 100 - distinct failing rule deductions); suggestion=1, warning=2, error=3'},
        'distribution': 'Bundled configuration, custom rule source and scoring data. Upstream Android Lint and detekt CLIs are installed directly from checksum-pinned artifacts; no Gradle/AGP plugin is loaded.',
        'combined_score': 'not defined'}
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print('Lint: Android/Compose official + Slack 1.6.1')
        for provider, count in sorted(Counter(r['provider'] for r in rules.values()).items()):
            print(f'detekt {provider}: {count} enabled rules')
        print(result['distribution'])
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print('compose-quality: ' + str(error), file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        sys.exit(130)
