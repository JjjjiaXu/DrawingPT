from __future__ import annotations

import argparse
import collections
import json
import xml.etree.ElementTree as ET
from pathlib import Path


SVG_TAGS = {
    "path",
    "line",
    "polyline",
    "polygon",
    "circle",
    "ellipse",
    "rect",
    "text",
    "g",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def scan_svg(path: Path) -> dict[str, object]:
    tag_counts: collections.Counter[str] = collections.Counter()
    attr_counts: collections.Counter[str] = collections.Counter()
    semantic_like: collections.Counter[str] = collections.Counter()

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return {"error": f"ET.ParseError: {exc}"}

    for elem in root.iter():
        tag = local_name(elem.tag)
        if tag in SVG_TAGS:
            tag_counts[tag] += 1
        for key, value in elem.attrib.items():
            clean_key = local_name(key)
            attr_counts[clean_key] += 1
            lower = clean_key.lower()
            if any(token in lower for token in ["class", "label", "semantic", "instance", "layer", "type"]):
                semantic_like[f"{clean_key}={value[:60]}"] += 1

    return {
        "tag_counts": dict(tag_counts),
        "top_attrs": dict(attr_counts.most_common(25)),
        "semantic_like_attrs": dict(semantic_like.most_common(25)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan a local FloorPlanCAD-style dataset directory.")
    parser.add_argument("--root", required=True, type=Path, help="Dataset root directory.")
    parser.add_argument("--sample", type=int, default=10, help="Number of SVG files to parse.")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional path for JSON summary.")
    args = parser.parse_args()

    root = args.root
    if not root.exists():
        raise SystemExit(f"Dataset root does not exist: {root}")

    files_by_ext: collections.Counter[str] = collections.Counter(
        p.suffix.lower() or "<no_ext>" for p in root.rglob("*") if p.is_file()
    )
    split_counts: dict[str, dict[str, int]] = {}
    for split in ["train", "val", "test", "train-00", "train-01", "test-00"]:
        split_root = root / split
        if split_root.exists():
            split_counts[split] = dict(
                collections.Counter(p.suffix.lower() or "<no_ext>" for p in split_root.rglob("*") if p.is_file())
            )

    svg_files = sorted(root.rglob("*.svg"))
    aggregate_tags: collections.Counter[str] = collections.Counter()
    aggregate_attrs: collections.Counter[str] = collections.Counter()
    aggregate_semantic_like: collections.Counter[str] = collections.Counter()
    errors: list[dict[str, str]] = []

    for svg in svg_files[: args.sample]:
        result = scan_svg(svg)
        if "error" in result:
            errors.append({"file": str(svg), "error": str(result["error"])})
            continue
        aggregate_tags.update(result["tag_counts"])  # type: ignore[arg-type]
        aggregate_attrs.update(result["top_attrs"])  # type: ignore[arg-type]
        aggregate_semantic_like.update(result["semantic_like_attrs"])  # type: ignore[arg-type]

    summary = {
        "root": str(root),
        "total_files_by_extension": dict(files_by_ext.most_common()),
        "split_counts": split_counts,
        "svg_file_count": len(svg_files),
        "sampled_svg_count": min(args.sample, len(svg_files)),
        "sample_tag_counts": dict(aggregate_tags.most_common()),
        "sample_top_attrs": dict(aggregate_attrs.most_common(40)),
        "sample_semantic_like_attrs": dict(aggregate_semantic_like.most_common(40)),
        "errors": errors,
    }

    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

