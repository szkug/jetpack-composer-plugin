#!/usr/bin/env python3
"""Maintainer-only deterministic custom rule JAR build; no Gradle or project mutation."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile
from ensure_analyzers import ROOT, ensure, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    # Rule source may intentionally differ from its release lock during maintenance.
    # Verify engine artifacts independently; never accept an invented compiler classpath.
    lock = json.loads((ROOT / 'scripts/verify/runtime/analyzers.lock.json').read_text())
    expected = {'lib/' + r['file']: r['sha256'] for r in lock['tools']['detekt']['artifacts']}
    manifest = None
    for candidate in sorted((Path.home() / '.local/share/compose-quality/analyzers').glob('detekt-*/runtime.json')):
        record = json.loads(candidate.read_text())
        if set(record.get('classpath', [])) == set(expected) and all(
                (candidate.parent / name).is_file() and sha(candidate.parent / name) == value
                for name, value in expected.items()):
            manifest = candidate
            break
    if manifest is None:
        native = ensure('detekt')
        if not native.get('runtime_manifest'):
            raise ValueError('Install the pinned managed detekt runtime before maintaining bundled rules')
        manifest = Path(native['runtime_manifest']);record = json.loads(manifest.read_text())
    cp = os.pathsep.join(str(manifest.parent / p) for p in record['classpath'])
    java = str(Path(os.environ['JAVA_HOME']) / 'bin/java') if os.environ.get('JAVA_HOME') else 'java'
    sources = sorted((ROOT / 'scripts/verify/rules/custom-compose-rule/src').rglob('*.kt'))
    with tempfile.TemporaryDirectory(prefix='compose-rules-compile-') as tmp:
        classes = Path(tmp) / 'classes';classes.mkdir()
        command = [java, '-cp', cp, 'org.jetbrains.kotlin.cli.jvm.K2JVMCompiler', '-no-stdlib', '-no-reflect',
                   '-classpath', cp, '-jvm-target', '17', '-d', str(classes), *map(str, sources)]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode:raise ValueError('Rule compiler failed: ' + result.stderr[-3000:])
        data = {p.relative_to(classes).as_posix(): p.read_bytes() for p in classes.rglob('*') if p.is_file()}
        base = ROOT / 'scripts/verify/rules/custom-compose-rule/src'
        data.update({p.relative_to(base).as_posix(): p.read_bytes() for p in base.rglob('*') if p.is_file() and p.suffix != '.kt'})
        defaults = (ROOT / 'scripts/verify/rules/detekt.yml').read_text().split('\nComposer:\n', 1)[1]
        data['config/config.yml'] = ('Composer:\n' + defaults).encode()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open('xb') as target, zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for name, value in sorted(data.items()):archive.writestr(zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0)), value)
    print(json.dumps({'jar': str(args.out.resolve()), 'sha256': sha(args.out)}))


if __name__ == '__main__':
    main()
