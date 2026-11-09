#!/usr/bin/env python3
"""Audit current evidence and calculate independent Lint and detekt scores."""
import argparse
import json

from score_common import digest, number, read_json, string_list, text_field
from diagnostics import POLICY
import engine

CATALOG = engine.CATALOG


def require_current(manifest):
    if not isinstance(manifest, dict) or manifest.get('schema_version') != 12:
        raise ValueError('schema_version 12 required; historical scoring protocols are not supported by this CLI')


def audit_manifest(manifest):
    require_current(manifest)
    return engine.audit(manifest)


def calculate(manifest, decisions, include_mean=False):
    require_current(manifest)
    return engine.calculate(manifest, decisions, include_mean)


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog='Scores are independent; no combined total or --mean option.')
    parser.add_argument('manifest', nargs='?')
    parser.add_argument('decisions', nargs='?')
    parser.add_argument('--audit', action='store_true', help='validate the frozen manifest')
    parser.add_argument('--catalog-hash', action='store_true', help='print the current canonical catalog hash')
    parser.add_argument('--lint-policy-hash', action='store_true', help='print the current Lint deduction policy hash')
    parser.add_argument('--diagnostic', action='store_true', help='allow explicitly incomplete tool results')
    args = parser.parse_args()
    try:
        if args.lint_policy_hash:
            print(digest(read_json(POLICY)))
        elif args.catalog_hash:
            print(digest(read_json(CATALOG)))
        else:
            if not args.manifest:
                parser.error('manifest required')
            manifest = read_json(args.manifest)
            if args.audit:
                result = audit_manifest(manifest)
            else:
                if not args.decisions:
                    parser.error('decisions required unless --audit')
                result = calculate(manifest, read_json(args.decisions))
                if result['publication_status'] == 'withheld' and not args.diagnostic:
                    raise ValueError('final score withheld: collect unresolved evidence; use --diagnostic only for work in progress')
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, OSError, ZeroDivisionError) as error:
        parser.exit(2, 'Invalid assessment input: ' + str(error) + '\n')


if __name__ == '__main__':
    raise SystemExit(main())
