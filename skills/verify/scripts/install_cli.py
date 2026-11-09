#!/usr/bin/env python3
"""Ensure an exact bundled CLI is available globally for the current user (macOS/Linux)."""
import argparse
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
from cli_bundle import APP_ID, COMMAND, copy_bundle, describe, verify

MARKER = '# compose-quality managed launcher'
PATH_START = '# >>> compose-quality PATH >>>'
PATH_END = '# <<< compose-quality PATH <<<'


def probe(executable):
    result = subprocess.run([str(executable), '--version', '--json'], capture_output=True, text=True, timeout=20)
    if result.returncode != 0:
        raise ValueError('Existing compose-quality failed its identity check; it was not overwritten: ' + str(executable))
    try:
        info = json.loads(result.stdout)
    except ValueError:
        raise ValueError('Existing command is not a recognized compose-quality installation: ' + str(executable))
    if info.get('application_id') != APP_ID:
        raise ValueError('Command name belongs to a different tool; it was not overwritten: ' + str(executable))
    return info


def configure_path(bin_dir):
    # Add an isolated block, never replace existing shell configuration.
    shell = Path(os.environ.get('SHELL', '')).name
    profiles = ['.zprofile', '.zshrc'] if shell == 'zsh' else ['.bash_profile', '.bashrc'] if shell == 'bash' else ['.profile'] if shell in ('sh', 'dash', '') else []
    block = (PATH_START + '\n_cq_bin=' + shlex.quote(str(bin_dir)) + '\n'
             'case ":$PATH:" in\n  *":$_cq_bin:"*) ;;\n  *) export PATH="$_cq_bin:$PATH" ;;\nesac\nunset _cq_bin\n' + PATH_END + '\n')
    modified = []
    for name in profiles:
        path = Path.home() / name
        text = path.read_text() if path.exists() else ''
        if PATH_START in text:
            if block not in text:
                raise ValueError('Existing compose-quality PATH block differs; left unchanged: ' + str(path))
            continue
        with path.open('a') as stream:
            stream.write(('\n' if text and not text.endswith('\n') else '') + '\n' + block)
        modified.append(str(path))
    return modified


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument('--bin-dir', type=Path, help='Default: ~/.local/bin')
    parser.add_argument('--data-dir', type=Path, help='Default: ~/.local/share/compose-quality')
    parser.add_argument('--check', action='store_true', help='Read-only: exit 1 if missing or not the exact bundled release')
    parser.add_argument('--no-path', action='store_true', help='Do not append a shell PATH block')
    args = parser.parse_args()
    if sys.version_info < (3, 9) or sys.platform not in ('darwin', 'linux'):
        raise ValueError('Installer supports macOS/Linux with Python 3.9+; it does not install Python/JDK/SDK')
    import fcntl
    source = args.source.expanduser().resolve()
    wanted = describe(source)
    bin_dir = (args.bin_dir or Path.home() / '.local/bin').expanduser().resolve()
    data_dir = (args.data_dir or Path.home() / '.local/share/compose-quality').expanduser().resolve()
    target = bin_dir / COMMAND
    found = target if target.exists() or target.is_symlink() else (Path(shutil.which(COMMAND)) if not args.bin_dir and shutil.which(COMMAND) else None)
    current = probe(found) if found else None
    exact = current is not None and current.get('bundle_sha256') == wanted['bundle_sha256']
    if args.check:
        from ensure_analyzers import ensure
        analyzers = [ensure(name, root=source, bin_dir=bin_dir if args.bin_dir else None,
                            data_dir=data_dir / 'analyzers' if args.data_dir else None, check=True)
                     for name in ['lint', 'detekt']]
        ready = exact and all(row['status'] != 'missing-or-incompatible' for row in analyzers)
        print(json.dumps({'status': 'ready' if ready else 'outdated' if current else 'missing',
                          'executable': str(found) if found else None, 'version': wanted['version'], 'analyzers': analyzers}))
        return 0 if ready else 1
    if exact:
        from ensure_analyzers import ensure
        analyzers = [ensure(name, root=source, bin_dir=bin_dir if args.bin_dir else None, data_dir=data_dir / 'analyzers' if args.data_dir else None) for name in ['lint', 'detekt']]
        profiles = []
        if not args.no_path and not args.bin_dir and str(bin_dir) not in os.environ.get('PATH', '').split(os.pathsep):
            profiles = configure_path(bin_dir)
        print(json.dumps({'status': 'already-installed', 'executable': str(found),
                          'version': wanted['version'], 'bundle_sha256': wanted['bundle_sha256'], 'path_profiles': profiles, 'analyzers': analyzers}))
        return 0
    before = target.read_bytes() if target.exists() else None
    if target.is_symlink() or before is not None and MARKER.encode() not in before:
        raise ValueError('Refusing to replace an unmanaged command: ' + str(target))
    data_dir.mkdir(parents=True, exist_ok=True)
    with (data_dir / 'install.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another compose-quality installation is active; retry after it completes')
        release = data_dir / 'versions' / (wanted['version'] + '-' + wanted['bundle_sha256'][:16])
        release.parent.mkdir(parents=True, exist_ok=True)
        if release.exists():
            verify(release)
        else:
            stage = Path(tempfile.mkdtemp(prefix='.stage-', dir=str(release.parent)))
            try:
                staged = copy_bundle(source, stage / 'payload')
                if staged['bundle_sha256'] != wanted['bundle_sha256']:
                    raise ValueError('Source changed during installation; retry from a stable bundle')
                os.replace(stage / 'payload', release)
            finally:
                shutil.rmtree(stage)
        if verify(release)['bundle_sha256'] != wanted['bundle_sha256']:
            raise ValueError('Source changed during installation; retry from a stable bundle')
        bin_dir.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or (target.read_bytes() if target.exists() else None) != before:
            raise ValueError('CLI command changed during installation; refusing to overwrite it')
        launcher = ('#!/bin/sh\n' + MARKER + '\n'
                    'export PYTHONDONTWRITEBYTECODE=1\nexec ' + shlex.quote(sys.executable) + ' ' +
                    shlex.quote(str(release / 'skills/verify/cli/main.py')) + ' "$@"\n')
        fd, temporary = tempfile.mkstemp(prefix='.compose-quality-', dir=str(bin_dir))
        try:
            with os.fdopen(fd, 'w') as stream:
                stream.write(launcher)
            Path(temporary).chmod(0o755)
            info = probe(Path(temporary))
            if info['bundle_sha256'] != wanted['bundle_sha256']:
                raise ValueError('Installed command does not match the bundled release')
            os.replace(temporary, target)
        finally:
            Path(temporary).unlink(missing_ok=True)
    from ensure_analyzers import ensure
    analyzers = [ensure(name, root=release, bin_dir=bin_dir if args.bin_dir else None, data_dir=data_dir / 'analyzers' if args.data_dir else None) for name in ['lint', 'detekt']]
    profiles = []
    if not args.no_path and not args.bin_dir and str(bin_dir) not in os.environ.get('PATH', '').split(os.pathsep):
        profiles = configure_path(bin_dir)
    print(json.dumps({'status': 'updated' if current else 'installed', 'executable': str(target),
                      'version': wanted['version'], 'bundle_sha256': wanted['bundle_sha256'],
                      'install_root': str(release), 'path_profiles': profiles, 'analyzers': analyzers,
                      'note': 'Use the absolute executable in the current process. New shells load an added PATH block. Older version directories remain for frozen scan receipts.'}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print('compose-quality installation failed: ' + str(error), file=sys.stderr)
        sys.exit(2)
