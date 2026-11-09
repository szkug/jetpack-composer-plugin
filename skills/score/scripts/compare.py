#!/usr/bin/env python3
"""Compare current candidates or reviews of identical frozen evidence."""
import argparse
import json

from calculate import require_current
from score_common import read_json
from engine import compare


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Lint and detekt remain independent; no combined total or --mean option.')
    parser.add_argument('manifest')
    parser.add_argument('decisions', nargs='+')
    parser.add_argument('--agreement', action='store_true', help='compare reviews of the same frozen source and evidence')
    parser.add_argument('--diagnostic', action='store_true', help='allow explicitly incomplete comparison results')
    args = parser.parse_args()
    try:
        manifest = read_json(args.manifest)
        require_current(manifest)
        result = compare(manifest, [read_json(path) for path in args.decisions], agreement=args.agreement)
        if result['publication_status'] == 'withheld' and not args.diagnostic:
            raise ValueError('final comparison withheld until required evidence is complete')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ZeroDivisionError) as error:
        parser.exit(2, 'Invalid comparison input: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
