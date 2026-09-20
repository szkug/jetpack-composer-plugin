#!/usr/bin/env python3
"""Inventory an Android XML/DataBinding layout and source-reference leads."""

from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ANDROID_NS = "{http://schemas.android.com/apk/res/android}"
BINDING_RE = re.compile(r"@=?\{(.+?)\}")
RESOURCE_RE = re.compile(r"@(?:[A-Za-z0-9_.]+:)?([A-Za-z0-9_]+)/([A-Za-z0-9_.]+)")


def first_line(path: Path, needle: str) -> int:
    for index, line in enumerate(path.read_text(errors="ignore").splitlines(), 1):
        if needle in line:
            return index
    return 1


def dedupe(items: list) -> list:
    seen: set[str] = set()
    output = []
    for item in items:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False)
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def layout_candidates(repo: Path, name: str) -> list[Path]:
    return sorted(
        path for path in repo.rglob(f"{name}.xml")
        if "/res/layout" in path.as_posix()
    )


def parse_layout(repo: Path, path: Path, seen: set[Path], result: dict) -> None:
    path = path.resolve()
    if path in seen:
        return
    seen.add(path)
    relative = path.relative_to(repo).as_posix()
    layout_id = Path(relative).stem
    result["layouts"].append(relative)
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        result["parseErrors"].append({"path": relative, "error": str(exc)})
        return

    for variable in root.findall("./data/variable"):
        name = variable.attrib.get("name", "")
        variable_needle = f'name="{name}"'
        result["bindingVariables"].append({
            "inventoryId": f"variable:{layout_id}:{name}",
            "name": name,
            "type": variable.attrib.get("type", ""),
            "evidence": f"{relative}:{first_line(path, variable_needle)}",
        })

    for element in root.iter():
        tag = element.tag.split("}")[-1]
        view_id = element.attrib.get(ANDROID_NS + "id")
        normalized_id = view_id.split("/")[-1] if view_id else None
        if normalized_id:
            result["views"].append({
                "inventoryId": f"view:{layout_id}:{normalized_id}",
                "id": normalized_id,
                "tag": tag,
                "evidence": f"{relative}:{first_line(path, normalized_id)}",
            })

        for attribute, value in element.attrib.items():
            attribute_name = attribute.split("}")[-1]
            for expression in BINDING_RE.findall(value):
                result["bindingExpressions"].append({
                    "layout": relative,
                    "viewId": normalized_id,
                    "attribute": attribute_name,
                    "expression": expression,
                    "twoWay": value.startswith("@={"),
                    "evidence": f"{relative}:{first_line(path, value)}",
                })
            for resource_type, resource_name in RESOURCE_RE.findall(value):
                result["resources"].append({
                    "type": resource_type,
                    "name": resource_name,
                    "evidence": f"{relative}:{first_line(path, value)}",
                })

        if tag in {"include", "ViewStub"}:
            layout_value = element.attrib.get("layout") or element.attrib.get(ANDROID_NS + "layout", "")
            included = layout_value.split("/")[-1]
            if included:
                matches = layout_candidates(repo, included)
                result["includes"].append({
                    "name": included,
                    "from": relative,
                    "candidates": [item.relative_to(repo).as_posix() for item in matches],
                })
                for match in matches:
                    parse_layout(repo, match, seen, result)


def binding_class_name(layout_name: str) -> str:
    return "".join(part.capitalize() for part in layout_name.split("_")) + "Binding"


def source_references(repo: Path, view_ids: set[str], layout_names: set[str]) -> list[dict]:
    hits = []
    ignored = {".git", ".gradle", "build", ".idea"}
    binding_names = {binding_class_name(name) for name in layout_names}
    for path in repo.rglob("*"):
        if not path.is_file() or path.suffix not in {".kt", ".java"}:
            continue
        if ignored.intersection(path.parts):
            continue
        try:
            content = path.read_text(errors="ignore")
        except OSError:
            continue
        lines = content.splitlines()
        binding_host = any(term in content for term in binding_names | layout_names)
        for index, line in enumerate(lines, 1):
            matched = []
            matched.extend(name for name in binding_names | layout_names if name in line)
            matched.extend(f"R.id.{view_id}" for view_id in view_ids if f"R.id.{view_id}" in line)
            if binding_host:
                matched.extend(f".{view_id}" for view_id in view_ids if f".{view_id}" in line)
            matched = sorted(set(matched))
            if matched:
                hits.append({
                    "evidence": f"{path.relative_to(repo).as_posix()}:{index}",
                    "terms": matched,
                    "excerpt": line.strip()[:240],
                })
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--layout", required=True, type=Path, action="append",
                        help="Root layout path, relative to repo or absolute; repeat for each replacement root")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    repo = args.repo.resolve()
    layouts = []
    for requested in args.layout:
        layout = requested if requested.is_absolute() else repo / requested
        layout = layout.resolve()
        if not layout.is_file():
            parser.error(f"layout not found: {layout}")
        try:
            layout.relative_to(repo)
        except ValueError:
            parser.error("layout must be inside repo")
        layouts.append(layout)

    result = {
        "schemaVersion": 2,
        "rootLayouts": [layout.relative_to(repo).as_posix() for layout in layouts],
        "layouts": [],
        "includes": [],
        "views": [],
        "bindingVariables": [],
        "bindingExpressions": [],
        "resources": [],
        "sourceReferences": [],
        "parseErrors": [],
        "reviewNote": "Search hits are leads; prove runtime reachability in migration-ledger.json.",
    }
    seen: set[Path] = set()
    for layout in layouts:
        parse_layout(repo, layout, seen, result)
    for key in ("layouts", "includes", "views", "bindingVariables", "bindingExpressions", "resources"):
        result[key] = dedupe(result[key])
    for index, item in enumerate(result["bindingExpressions"], 1):
        stable_view = item.get("viewId") or "root"
        layout_id = Path(item["layout"]).stem
        item["inventoryId"] = f"binding:{layout_id}:{stable_view}:{item['attribute']}:{index}"

    view_ids = {entry["id"] for entry in result["views"]}
    layout_names = {Path(item).stem for item in result["layouts"]}
    result["sourceReferences"] = source_references(repo, view_ids, layout_names)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({
        "ok": not result["parseErrors"],
        "layouts": len(result["layouts"]),
        "views": len(result["views"]),
        "bindingVariables": len(result["bindingVariables"]),
        "bindingExpressions": len(result["bindingExpressions"]),
        "sourceReferences": len(result["sourceReferences"]),
        "out": str(args.out.resolve()),
    }, ensure_ascii=False))
    return 0 if not result["parseErrors"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
