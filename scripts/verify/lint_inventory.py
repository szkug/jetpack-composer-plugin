"""Collect the native registry without ID filtering and build an all-rule scan policy."""
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import xml.etree.ElementTree as ET
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'score'))
from lint_registry import parse_inventory
from rule_policy import load_policy, policy_digest


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()



def collect(native, jars, out):
    if load_policy()['lint']['activation'] != 'all-registered':
        raise ValueError('Unsupported built-in Lint activation policy')
    executable = Path(native['executable'])
    runtime = executable.parent.parent / 'runtime.json'
    if native.get('external') or not runtime.is_file():
        raise ValueError('All-rule scoring requires a managed Lint runtime with exact provider receipts')
    record = json.loads(runtime.read_text())
    providers = {'runtime:' + name: value for name, value in record['files'].items() if name.endswith('.jar')}
    for name, expected in record['files'].items():
        if sha(runtime.parent / name) != expected:
            raise ValueError('Lint runtime integrity mismatch: ' + name)
    providers.update({'project:' + Path(p).name + ':' + sha(p): sha(p) for p in jars})
    env = dict(os.environ)
    env.pop('LINT_JARS', None)
    env['ANDROID_LINT_JARS'] = os.pathsep.join(map(str, jars))
    outputs = {}
    for flag in ('list', 'show'):
        result = subprocess.run([str(executable), '--' + flag], env=env, capture_output=True, text=True)
        if result.returncode or result.stderr.strip():
            raise ValueError('Lint registry discovery failed: ' + result.stderr[:2000])
        outputs[flag] = result.stdout
        (out / ('lint-' + flag + '.txt')).write_text(result.stdout)
    severities = parse_inventory(outputs['list'], outputs['show'])
    inventory = {'schema_version': 1, 'mode': 'all-registered', 'providers': providers,
                 'rule_policy_sha256': policy_digest(), 'rules': severities, 'discovery_output': outputs, 'discovery': {key: hashlib.sha256(value.encode()).hexdigest()
                                                  for key, value in outputs.items()}}
    (out / 'lint-inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    config = ET.Element('lint')
    for rule, severity in severities.items():
        ET.SubElement(config, 'issue', id=rule, severity={'Information': 'informational', 'Hint': 'informational'}.get(severity, severity.lower()))
    ET.ElementTree(config).write(out / 'all-rules-lint.xml', encoding='utf-8', xml_declaration=True)
    return inventory
