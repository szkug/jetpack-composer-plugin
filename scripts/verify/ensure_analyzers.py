#!/usr/bin/env python3
"""Install standalone Android Lint / detekt CLIs without Gradle, AGP or a project."""
import argparse
import concurrent.futures
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MARKER = '# composer standalone analyzer launcher'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def lock_data(root):
    p = root / 'scripts/verify/runtime/analyzers.lock.json'
    lock = json.loads(p.read_text())
    for name, expected in lock['rules'].items():
        if sha(root / name) != expected:
            raise ValueError('Bundled rule JAR changed: ' + name)
    if sha(root / 'scripts/verify/rules/detekt.yml') != lock['config_sha256']:
        raise ValueError('Bundled config differs from analyzer lock')
    for name, expected in lock['custom_source_sha256'].items():
        if sha(root / name) != expected:
            raise ValueError('Custom rule source differs from prebuilt JAR; rebuild the release')
    return lock, sha(p)



def rule_path(root, lock, name):
    paths = [Path(path) for path in lock['rules'] if Path(path).name == name]
    if len(paths) != 1:
        raise ValueError('Expected one locked rule artifact: ' + name)
    path = (Path(root) / paths[0]).resolve()
    if not path.is_relative_to((Path(root) / 'scripts/verify/rules').resolve()):
        raise ValueError('Rule artifact is outside the bundled rules directory')
    return path


def existing_version(path, tool, version):
    if not path or not Path(path).is_file():
        return False
    try:
        p = subprocess.run([str(path), '--version'], capture_output=True, text=True, timeout=30)
        output = (p.stdout + p.stderr).strip()
        return p.returncode == 0 and (output == version if tool == 'detekt' else output == 'lint: version ' + version)
    except (OSError, subprocess.TimeoutExpired):
        return False


def fetch(row, destination):
    # Local caches are only an optimization. They never invoke or require Gradle/Maven.
    g, a, v = row['coordinate'].split(':')
    candidates = list((Path.home() / '.gradle/caches/modules-2/files-2.1' / g / a / v).glob('*/' + a + '-' + v + '.jar'))
    # Reuse byte-verified artifacts when only our policy/configuration changes.
    candidates += list((Path.home() / '.local/share/compose-quality/analyzers').glob('*/lib/' + row['file']))
    candidates.append(Path.home() / '.m2/repository' / g.replace('.', '/') / a / v / (a + '-' + v + '.jar'))
    for path in candidates:
        if path.is_file() and sha(path) == row['sha256']:
            shutil.copyfile(path, destination)
            return
    if not row['url'].startswith(('https://dl.google.com/dl/android/maven2/', 'https://repo.maven.apache.org/maven2/')):
        raise ValueError('Unexpected analyzer download origin')
    with urllib.request.urlopen(row['url'], timeout=60) as response, destination.open('wb') as target:
        shutil.copyfileobj(response, target)
    if sha(destination) != row['sha256']:
        raise ValueError('Downloaded analyzer checksum mismatch: ' + row['coordinate'])


def ensure(tool, root=ROOT, bin_dir=None, data_dir=None, check=False):
    root = Path(root).resolve()
    lock, fingerprint = lock_data(root)
    spec = lock['tools'][tool]
    custom_bin = bin_dir is not None
    bin_dir = Path(bin_dir or Path.home() / '.local/bin').expanduser().resolve()
    data_dir = Path(data_dir or Path.home() / '.local/share/compose-quality/analyzers').expanduser().resolve()
    target = bin_dir / tool
    found = (str(target) if target.is_file() else None) if custom_bin else shutil.which(tool) or (str(target) if target.is_file() else None)
    # Native external installations can be reused, but are never replaced or reconfigured.
    managed = bool(found and Path(found).is_file() and not Path(found).is_symlink() and MARKER.encode() in Path(found).read_bytes()[:256])
    runtime_key = hashlib.sha256((fingerprint + sha(root / 'scripts/verify/native_launch.py')).encode()).hexdigest()
    release = data_dir / (tool + '-' + spec['version'] + '-' + runtime_key[:16])
    if found and not managed and existing_version(found, tool, spec['cli_version']):
        return {'tool': tool, 'status': 'reused-external', 'executable': str(Path(found).resolve()),
                'version': spec['cli_version'], 'distribution_version': spec['version'], 'external': True}
    ready = release.is_dir() and existing_version(release / 'bin' / tool, tool, spec['cli_version'])
    if check:
        return {'tool': tool, 'status': 'ready' if ready else 'missing-or-incompatible',
                'executable': str(release / 'bin' / tool) if ready else None, 'version': spec['cli_version'], 'external': False}
    java = Path(os.environ['JAVA_HOME']) / 'bin/java' if os.environ.get('JAVA_HOME') else shutil.which('java')
    if not java or not Path(java).is_file():
        raise ValueError('Install a JDK 17+ or set JAVA_HOME before installing analyzer CLIs')
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / 'install.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not ready:
            if release.exists():
                raise ValueError('Existing analyzer installation is damaged; retained for inspection: ' + str(release))
            stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=str(data_dir)))
            try:
                (stage / 'lib').mkdir(); (stage / 'rules').mkdir(); (stage / 'bin').mkdir()
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(lambda r: fetch(r, stage / 'lib' / r['file']), spec['artifacts']))
                rule_names = ['compose-lint-checks-1.6.1.jar'] if tool == 'lint' else ['detekt-0.6.8.jar', 'common-detekt-0.6.8.jar', 'composer-quality-rules.jar']
                for name in rule_names:
                    shutil.copyfile(rule_path(root, lock, name), stage / 'rules' / name)
                shutil.copyfile(root / 'scripts/verify/rules/detekt.yml', stage / 'detekt.yml')
                shutil.copyfile(root / 'scripts/verify/native_launch.py', stage / 'launch.py')
                record = {'tool': tool, 'version': spec['cli_version'], 'distribution_version': spec['version'],
                          'lock_sha256': fingerprint, 'main_class': spec['main_class'],
                          'classpath': ['lib/' + r['file'] for r in spec['artifacts']],
                          'rule_jars': ['rules/' + name for name in rule_names],
                          'files': {p.relative_to(stage).as_posix(): sha(p) for p in stage.rglob('*') if p.is_file()}}
                (stage / 'runtime.json').write_text(json.dumps(record, indent=2) + '\n')
                # Relative launch paths also work before the final directory is activated.
                launcher = '#!/bin/sh\n' + MARKER + '\n_cq_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)\nexec ' + shlex.quote(sys.executable) + ' "$_cq_dir/launch.py" "$_cq_dir/runtime.json" "$@"\n'
                native = stage / 'bin' / tool; native.write_text(launcher); native.chmod(0o755)
                if not existing_version(native, tool, spec['cli_version']):
                    raise ValueError('Installed upstream CLI failed its version check (JDK 17+ required)')
                os.replace(stage, release)
            finally:
                if stage.exists():shutil.rmtree(stage)
        bin_dir.mkdir(parents=True, exist_ok=True)
        target_managed = target.is_file() and not target.is_symlink() and MARKER.encode() in target.read_bytes()[:256]
        collision = target.exists() and not target_managed or target.is_symlink()
        if not collision:
            launcher = '#!/bin/sh\n' + MARKER + '\nexec ' + shlex.quote(str(release / 'bin' / tool)) + ' "$@"\n'
            if target.is_file() and target.read_text() == launcher:
                return {'tool': tool, 'status': 'already-installed', 'executable': str(release / 'bin' / tool), 'global_command': str(target),
                        'version': spec['cli_version'], 'distribution_version': spec['version'], 'external': False,
                        'runtime_manifest': str(release / 'runtime.json'), 'collision_preserved': False}
            fd, temporary = tempfile.mkstemp(prefix='.' + tool + '-', dir=str(bin_dir))
            try:
                with os.fdopen(fd, 'w') as stream:stream.write(launcher)
                Path(temporary).chmod(0o755)
                os.replace(temporary, target)
            finally:Path(temporary).unlink(missing_ok=True)
    return {'tool': tool, 'status': 'already-installed' if ready else 'installed',
            'executable': str(release / 'bin' / tool), 'global_command': None if collision else str(target),
            'version': spec['cli_version'], 'distribution_version': spec['version'], 'external': False,
            'runtime_manifest': str(release / 'runtime.json'), 'collision_preserved': bool(collision)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tool', choices=['lint', 'detekt', 'all'], default='all')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--bin-dir', type=Path)
    parser.add_argument('--data-dir', type=Path)
    args = parser.parse_args()
    rows = [ensure(name, bin_dir=args.bin_dir, data_dir=args.data_dir, check=args.check)
            for name in (['lint', 'detekt'] if args.tool == 'all' else [args.tool])]
    profiles = []
    if not args.check and not args.bin_dir and str(Path.home() / '.local/bin') not in os.environ.get('PATH', '').split(os.pathsep):
        from install_cli import configure_path
        profiles = configure_path(Path.home() / '.local/bin')
    print(json.dumps({'analyzers': rows, 'path_profiles': profiles}, indent=2))
    return 1 if any(row['status'] == 'missing-or-incompatible' for row in rows) else 0


if __name__ == '__main__':
    try:sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('Analyzer CLI installation failed: ' + str(error), file=sys.stderr);sys.exit(2)
