#!/bin/sh
# Local, inspectable bootstrap. No curl|sh, sudo, pip mutation or automatic build.
set -eu
cq_script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for cq_python in python3 python; do
    if command -v "$cq_python" >/dev/null 2>&1 && "$cq_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
        exec "$cq_python" "$cq_script_dir/install_cli.py" "$@"
    fi
done
printf '%s\n' 'compose-quality requires Python 3.9+. No compatible interpreter was found; install Python and rerun this bootstrap. No system files were modified.' >&2
exit 2
