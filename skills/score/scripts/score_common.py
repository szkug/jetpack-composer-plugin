"""JSON validation and deterministic arithmetic shared by the current scorer."""
import hashlib
import json
from decimal import Decimal
from pathlib import Path


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('duplicate JSON key: ' + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_pairs)


def digest(value):
    """Canonical JSON hash, independent of whitespace and object key order."""
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def number(value):
    return str(Decimal(value.numerator) / Decimal(value.denominator))


def text_field(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError('nonempty text required: ' + key)
    return value


def string_list(value, label):
    if not isinstance(value, list) or not value or any(
            not isinstance(x, str) or not x.strip() for x in value):
        raise ValueError('nonempty string list required: ' + label)
    if len(set(value)) != len(value):
        raise ValueError('duplicate entries: ' + label)
    return value
