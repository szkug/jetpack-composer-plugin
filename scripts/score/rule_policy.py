"""Single built-in rule policy consumed by scanners and the scorer."""
import json
from pathlib import Path
from score_common import digest

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / 'references/verify/rule-policy.json'


def load_policy():
    return json.loads(POLICY.read_text())


def policy_digest():
    return digest(load_policy())


def classification(severity):
    policy = load_policy()
    return policy['native_severity_classes'][severity]


def deduction(severity):
    policy = load_policy()
    return policy['classes'][policy['native_severity_classes'][severity]]['deduction']
