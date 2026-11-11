#!/bin/sh
# Install/ensure the bundled compose-quality command for this user.
set -eu
cq_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec sh "$cq_root/scripts/verify/ensure_cli.sh" "$@"
