#!/usr/bin/env python3
"""Build a relocatable CLI archive; no publishing and no external Python dependencies."""
import argparse
import gzip
import json
from pathlib import Path
import tarfile
import tempfile
import sys
from cli_bundle import copy_bundle, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--out', type=Path, required=True, help='New .tar.gz archive path')
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='compose-quality-build-') as temporary:
        payload = Path(temporary) / 'payload'
        record = copy_bundle(args.source.resolve(), payload)
        # Exclusive create: never replace another release artifact silently.
        with args.out.open('xb') as raw:
            with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as compressed:
                with tarfile.open(fileobj=compressed, mode='w') as archive:
                    for path in sorted(p for p in payload.rglob('*') if p.is_file()):
                        name = 'compose-quality-' + record['version'] + '/' + path.relative_to(payload).as_posix()
                        info = tarfile.TarInfo(name)
                        info.size = path.stat().st_size
                        info.mode = 0o755 if path.suffix == '.sh' else 0o644
                        info.mtime = 0
                        with path.open('rb') as stream:
                            archive.addfile(info, stream)
    print(json.dumps({'archive': str(args.out.resolve()), 'sha256': sha(args.out),
                      'version': record['version'], 'bundle_sha256': record['bundle_sha256']}))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError) as error:
        print('CLI packaging failed: ' + str(error), file=sys.stderr)
        sys.exit(2)
