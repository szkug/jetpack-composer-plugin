"""Build and verify the self-contained, standard-library-only CLI distribution."""
import hashlib
import json
import re
import shutil
from pathlib import Path

APP_ID = 'dev.composer.compose-quality'
COMMAND = 'compose-quality'
PROTOCOL = 12


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def source_files(root):
    names = ['install-cli.sh', 'install-analyzers.sh', 'CLI.md', '.codex-plugin/plugin.json', 'skills/verify/cli/main.py',
             'skills/verify/scripts/rules/detekt.yml']
    names += ['skills/verify/scripts/' + name for name in (
        'incremental_lint.py', 'incremental_detekt.py', 'standalone_scan.py',
        'ensure_analyzers.py', 'native_launch.py', 'build_rule_jar.py', 'cli_bundle.py', 'install_cli.py',
        'build_cli.py', 'ensure_cli.sh')]
    # Explicit current runtime closure: examples, registries and archived profiles are not CLI payload.
    names += ['skills/score/scripts/' + name for name in (
        'calculate.py', 'compare.py', 'engine.py', 'score_common.py', 'diagnostics.py')]
    names += ['skills/score/references/' + name for name in (
        'catalog.json', 'lint-policy.json')]
    names += ['skills/verify/references/' + name for name in ('coverage.json', 'acceptance-boundaries.json')]
    for pattern in ('skills/verify/scripts/runtime/**/*', 'skills/verify/scripts/rules/**/*'):
        names += [p.relative_to(root).as_posix() for p in root.glob(pattern) if p.is_file()]
    for name in sorted(set(names)):
        p = root / name
        if not p.is_file() or p.is_symlink():
            raise ValueError('Missing/nonregular CLI payload file: ' + name)
        yield name


def describe(root):
    catalog = json.loads((root / 'skills/score/references/catalog.json').read_text())
    version = json.loads((root / '.codex-plugin/plugin.json').read_text())['version']
    if not isinstance(version, str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?', version):
        raise ValueError('Invalid CLI release version')
    if sha(root / 'skills/verify/scripts/rules/detekt.yml') != catalog['default_config_sha256']:
        raise ValueError('Bundled YAML differs from the scoring catalog')
    files = {name: sha(root / name) for name in source_files(root)}
    payload = {'application_id': APP_ID, 'command': COMMAND, 'version': version,
               'protocol': PROTOCOL, 'python_minimum': '3.9', 'files': files,
               'detekt_version': catalog['detekt_version'],
               'compose_rules_version': catalog['compose_rules_version'],
               'composer_rules_version': catalog['composer_rules_version'],
               'enabled_detekt_rules': sum(row['enabled'] for row in catalog['rules'].values())}
    payload['bundle_sha256'] = digest(payload)
    return payload


def verify(root):
    record = json.loads((root / 'cli-manifest.json').read_text())
    content = {k: v for k, v in record.items() if k != 'bundle_sha256'}
    if record.get('application_id') != APP_ID or digest(content) != record.get('bundle_sha256'):
        raise ValueError('Invalid CLI bundle manifest')
    for name, expected in record['files'].items():
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe bundle path')
        path = root / relative
        if not path.is_file() or path.is_symlink() or sha(path) != expected:
            raise ValueError('CLI bundle integrity mismatch: ' + name)
    return record


def copy_bundle(source, destination):
    record = describe(source)
    destination.mkdir(parents=True, exist_ok=False)
    for name in record['files']:
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
        target.chmod(0o755 if target.suffix == '.sh' else 0o644)
    (destination / 'cli-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
    verify(destination)
    return record
