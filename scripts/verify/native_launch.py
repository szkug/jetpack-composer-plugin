#!/usr/bin/env python3
"""Launch an installed upstream CLI, checking its locked local runtime first."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    manifest = Path(sys.argv[1])
    record = json.loads(manifest.read_text())
    root = manifest.parent
    for name, expected in record['files'].items():
        p = root / name
        if Path(name).is_absolute() or '..' in Path(name).parts or not p.is_file() or p.is_symlink():
            raise ValueError('Invalid analyzer file: ' + name)
        if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
            raise ValueError('Analyzer runtime changed: ' + name)
    java = str(Path(os.environ['JAVA_HOME']) / 'bin/java') if os.environ.get('JAVA_HOME') else shutil.which('java')
    if not java:
        raise ValueError('JDK 17+ is required; JAVA_HOME or java on PATH is missing')
    args = sys.argv[2:]
    if record['tool'] == 'detekt':
        if not any(x in args for x in ('--plugins', '-p')):
            args = ['--plugins', os.pathsep.join(str(root / p) for p in record['rule_jars']), *args]
        if not any(x in args for x in ('--config', '-c', '--config-resource', '-cr')):
            args = ['--config', str(root / 'detekt.yml'), *args]
    elif '--lint-rule-jars' not in args:
        args = ['--lint-rule-jars', os.pathsep.join(str(root / p) for p in record['rule_jars']), *args]
    command = [java, '-Djava.awt.headless=true', '-cp', os.pathsep.join(str(root / p) for p in record['classpath']), record['main_class'], *args]
    env = dict(os.environ)
    if record['tool'] == 'lint':
        # --project metadata overrides per-project rule flags. Global discovery also
        # makes the bundled registry visible to --show/--list and plain CLI use.
        bundled = os.pathsep.join(str(root / p) for p in record['rule_jars'])
        env['ANDROID_LINT_JARS'] = bundled + (os.pathsep + env['ANDROID_LINT_JARS'] if env.get('ANDROID_LINT_JARS') else '')
    return subprocess.call(command, env=env)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print('Analyzer CLI: ' + str(error), file=sys.stderr)
        sys.exit(2)
