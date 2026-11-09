#!/bin/sh
# Install the upstream Android Lint and detekt CLIs with bundled Compose rules.
set -eu
cq_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
for cq_python in python3 python; do
    if command -v "$cq_python" >/dev/null 2>&1 && "$cq_python" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
        exec "$cq_python" "$cq_root/skills/verify/scripts/ensure_analyzers.py" "$@"
    fi
done
printf '%s\n' 'Python 3.9+ is required to install the analyzer CLIs.' >&2
exit 2
