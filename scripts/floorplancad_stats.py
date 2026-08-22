from __future__ import annotations

import argparse
import collections
import csv
import json
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path


CLASS_NAMES = {
    1: "single door",
    2: "double door",
    3: "sliding door",
    4: "folding door",
    5: "revolving door",
    6: "rolling door",
    7: "window",
    8: "bay window",
    9: "blind window",
    10: "opening symbol",
    11: "sofa",
    12: "bed",
    13: "chair",
    14: "table",
    15: "TV cabinet",
    16: "Wardrobe",
    17: "cabinet",
    18: "gas stove",
    19: "sink",
    20: "refrigerator",
    21: "airconditioner",
    22: "bath",
    23: "bath tub",
    24: "washing machine",
    25: "squat toilet",
    26: "urinal",
    27: "toilet",
    28: "stairs",
    29: "elevator",
    30: "escalator",
    31: "row chairs",
    32: "parking spot",
    33: "wall",
    34: "curtain wall",
    35: "railing",
}


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def int_attr(attrs: dict[str, str], name: str) -> int | None:
    for key, value in attrs.items():
        if local_name(key).lower() == name.lower():
            try:
                return int(value)
            except ValueError:
                return None
    return None


def inspect_svg(path: Path) -> dict[str, object]:
    root = ET.parse(path).getroot()
    semantic_counts: collections.Counter[int] = collections.Counter()
    instance_ids: set[int] = set()
    primitive_count = 0
    tag_counts: collections.Counter[str] = collections.Counter()

    for elem in root.iter():
        tag = local_name(elem.tag)
        if tag in {"path", "line", "polyline", "polygon", "circle", "ellipse", "rect", "text"}:
            primitive_count += 1
            tag_counts[tag] += 1
        semantic_id = int_attr(elem.attrib, "semanticId")
        instance_id = int_attr(elem.attrib, "instanceId")
        if semantic_id is not None:
            semantic_counts[semantic_id] += 1
        if instance_id is not None and instance_id >= 0:
            instance_ids.add(instance_id)

    return {
        "file": str(path),
        "primitive_count": primitive_count,
        "instance_count": len(instance_ids),
        "semantic_counts": dict(semantic_counts),
        "tag_counts": dict(tag_counts),
    }


def summarize(records: list[dict[str, object]]) -> dict[str, object]:
    semantic_counts: collections.Counter[int] = collections.Counter()
    tag_counts: collections.Counter[str] = collections.Counter()
    primitive_counts: list[int] = []
    instance_counts: list[int] = []

    for record in records:
        semantic_counts.update(record["semantic_counts"])  # type: ignore[arg-type]
        tag_counts.update(record["tag_counts"])  # type: ignore[arg-type]
        primitive_counts.append(int(record["primitive_count"]))
        instance_counts.append(int(record["instance_count"]))

    def describe(values: list[int]) -> dict[str, float | int]:
        if not values:
            return {}
        return {
            "min": min(values),
            "median": statistics.median(values),
            "mean": round(statistics.mean(values), 2),
            "max": max(values),
        }

    return {
        "file_count": len(records),
        "primitive_count_per_file": describe(primitive_counts),
        "instance_count_per_file": describe(instance_counts),
        "tag_counts": dict(tag_counts.most_common()),
        "semantic_counts": {
            str(class_id): {
                "name": CLASS_NAMES.get(class_id, "<unknown/background>"),
                "count": count,
            }
            for class_id, count in semantic_counts.most_common()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute full FloorPlanCAD SVG semantic/instance statistics.")
    parser.add_argument("--root", required=True, type=Path, help="Directory containing SVG files.")
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument("--csv-out", type=Path, default=None)
    args = parser.parse_args()

    svg_files = sorted(args.root.rglob("*.svg"))
    if not svg_files:
        raise SystemExit(f"No SVG files found under: {args.root}")

    records = [inspect_svg(path) for path in svg_files]
    summary = summarize(records)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")
    if args.csv_out:
        args.csv_out.parent.mkdir(parents=True, exist_ok=True)
        with args.csv_out.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["file", "primitive_count", "instance_count"])
            for record in records:
                writer.writerow([record["file"], record["primitive_count"], record["instance_count"]])


if __name__ == "__main__":
    main()

