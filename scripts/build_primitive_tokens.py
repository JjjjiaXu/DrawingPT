from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from floorplancad_quantity_proxy import (
    CLASS_NAMES,
    PATH_TOKEN_RE,
    POINT_RE,
    SVG_GEOMETRY_TAGS,
    float_attr,
    geometry_length,
    int_attr,
    local_name,
    split_roots,
)


TOKEN_VERSION = "floorplancad-primitive-token-v0.1"
DEFAULT_WINDOW_SIZE = 2048


@dataclass
class FileTokenStats:
    split: str
    file: str
    token_count: int = 0
    semantic_token_count: int = 0
    unknown_semantic_token_count: int = 0
    text_element_count: int = 0
    class_ids: set[int] = field(default_factory=set)
    tag_counts: collections.Counter[str] = field(default_factory=collections.Counter)
    path_command_counts: collections.Counter[str] = field(default_factory=collections.Counter)
    viewbox_min_x: float | None = None
    viewbox_min_y: float | None = None
    viewbox_width: float | None = None
    viewbox_height: float | None = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_number(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, digits)


def attr_value(attrs: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in attrs.items():
        if local_name(key).lower() == target:
            return value
    return None


def parse_numeric_attr(attrs: dict[str, str], name: str) -> float | None:
    value = attr_value(attrs, name)
    if not value:
        return None
    match = POINT_RE.search(value)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def parse_viewbox(root: ET.Element) -> tuple[float | None, float | None, float | None, float | None]:
    viewbox = attr_value(root.attrib, "viewBox")
    if viewbox:
        values = [float(x) for x in POINT_RE.findall(viewbox)]
        if len(values) >= 4:
            return values[0], values[1], values[2], values[3]
    width = parse_numeric_attr(root.attrib, "width")
    height = parse_numeric_attr(root.attrib, "height")
    if width is not None and height is not None:
        return 0.0, 0.0, width, height
    return None, None, None, None


def bounds_from_points(points: Iterable[tuple[float, float]]) -> tuple[float, float, float, float] | None:
    pts = list(points)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def path_bbox_rough(d: str) -> tuple[float, float, float, float] | None:
    """Return a stable rough path bbox without external SVG geometry libraries.

    This intentionally prefers reproducibility and zero dependency over exact
    arc/Bezier envelopes. It is good enough for a v0 token feature and is
    explicitly documented as an approximation in the generated summary.
    """

    values = [float(x) for x in POINT_RE.findall(d)]
    if len(values) < 2:
        return None
    return bounds_from_points(zip(values[0::2], values[1::2]))


def geometry_bbox(tag: str, attrs: dict[str, str]) -> tuple[float, float, float, float] | None:
    if tag == "path":
        return path_bbox_rough(attrs.get("d", ""))
    if tag == "circle":
        cx = float_attr(attrs, "cx") or 0.0
        cy = float_attr(attrs, "cy") or 0.0
        r = float_attr(attrs, "r") or 0.0
        return cx - r, cy - r, cx + r, cy + r
    if tag == "ellipse":
        cx = float_attr(attrs, "cx") or 0.0
        cy = float_attr(attrs, "cy") or 0.0
        rx = float_attr(attrs, "rx") or 0.0
        ry = float_attr(attrs, "ry") or 0.0
        return cx - rx, cy - ry, cx + rx, cy + ry
    if tag == "line":
        x1 = float_attr(attrs, "x1") or 0.0
        y1 = float_attr(attrs, "y1") or 0.0
        x2 = float_attr(attrs, "x2") or 0.0
        y2 = float_attr(attrs, "y2") or 0.0
        return bounds_from_points([(x1, y1), (x2, y2)])
    if tag in {"polyline", "polygon"}:
        values = [float(x) for x in POINT_RE.findall(attrs.get("points", ""))]
        return bounds_from_points(zip(values[0::2], values[1::2]))
    if tag == "rect":
        x = float_attr(attrs, "x") or 0.0
        y = float_attr(attrs, "y") or 0.0
        width = float_attr(attrs, "width") or 0.0
        height = float_attr(attrs, "height") or 0.0
        return x, y, x + width, y + height
    return None


def normalize_bbox(
    bbox: tuple[float, float, float, float] | None,
    viewbox: tuple[float | None, float | None, float | None, float | None],
) -> tuple[float | None, float | None, float | None, float | None]:
    if bbox is None:
        return None, None, None, None
    min_x, min_y, width, height = viewbox
    if min_x is None or min_y is None or not width or not height:
        return None, None, None, None
    x0, y0, x1, y1 = bbox
    return (
        (x0 - min_x) / width,
        (y0 - min_y) / height,
        (x1 - min_x) / width,
        (y1 - min_y) / height,
    )


def stable_style_hash(attrs: dict[str, str]) -> str:
    style_key = "|".join(
        [
            attr_value(attrs, "stroke") or "",
            attr_value(attrs, "fill") or "",
            attr_value(attrs, "stroke-width") or "",
            attr_value(attrs, "opacity") or "",
        ]
    )
    return sha256_text(style_key)[:12]


def token_from_element(
    idx: int,
    tag: str,
    attrs: dict[str, str],
    viewbox: tuple[float | None, float | None, float | None, float | None],
) -> dict[str, object]:
    bbox = geometry_bbox(tag, attrs)
    norm_bbox = normalize_bbox(bbox, viewbox)
    if bbox is None:
        width = height = center_x = center_y = area_proxy = None
    else:
        x0, y0, x1, y1 = bbox
        width = max(0.0, x1 - x0)
        height = max(0.0, y1 - y0)
        center_x = x0 + width / 2
        center_y = y0 + height / 2
        area_proxy = width * height

    stroke_width = float_attr(attrs, "stroke-width")
    fill = attr_value(attrs, "fill")
    stroke = attr_value(attrs, "stroke")
    class_id = int_attr(attrs, "semanticId")
    instance_id = int_attr(attrs, "instanceId")

    return {
        "idx": idx,
        "token_version": TOKEN_VERSION,
        "tag": tag,
        "semantic_id": class_id,
        "semantic_name": CLASS_NAMES.get(class_id, "<unknown>") if class_id is not None else None,
        "instance_id": instance_id,
        "bbox": [normalize_number(v, 3) for v in bbox] if bbox is not None else None,
        "bbox_norm": [normalize_number(v, 6) for v in norm_bbox],
        "center": [normalize_number(center_x, 3), normalize_number(center_y, 3)],
        "size": [normalize_number(width, 3), normalize_number(height, 3)],
        "length_proxy": normalize_number(geometry_length(tag, attrs), 3),
        "area_proxy": normalize_number(area_proxy, 3),
        "stroke_width": normalize_number(stroke_width, 3),
        "has_fill": bool(fill and fill.lower() != "none"),
        "has_stroke": bool(stroke and stroke.lower() != "none"),
        "style_hash": stable_style_hash(attrs),
    }


def inspect_svg(
    split: str,
    path: Path,
    write_tokens: bool,
    token_out: Path | None,
) -> tuple[FileTokenStats, Path | None]:
    root = ET.parse(path).getroot()
    viewbox = parse_viewbox(root)
    stats = FileTokenStats(split=split, file=path.name)
    stats.viewbox_min_x, stats.viewbox_min_y, stats.viewbox_width, stats.viewbox_height = viewbox

    token_stream = None
    token_path = None
    if write_tokens:
        if token_out is None:
            raise ValueError("token_out is required when write_tokens=True")
        token_path = token_out / split / f"{path.stem}.jsonl"
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_stream = token_path.open("w", encoding="utf-8")

    try:
        token_idx = 0
        for elem in root.iter():
            tag = local_name(elem.tag)
            if tag == "text":
                stats.text_element_count += 1
            if tag not in SVG_GEOMETRY_TAGS:
                continue

            attrs = elem.attrib
            stats.token_count += 1
            stats.tag_counts[tag] += 1
            if tag == "path":
                stats.path_command_counts.update(
                    token.upper()
                    for token in PATH_TOKEN_RE.findall(attrs.get("d", ""))
                    if len(token) == 1 and token.isalpha()
                )

            class_id = int_attr(attrs, "semanticId")
            if class_id is not None:
                stats.semantic_token_count += 1
                if class_id in CLASS_NAMES:
                    stats.class_ids.add(class_id)
                else:
                    stats.unknown_semantic_token_count += 1

            if token_stream is not None:
                token = token_from_element(token_idx, tag, attrs, viewbox)
                token_stream.write(json.dumps(token, ensure_ascii=False, separators=(",", ":")) + "\n")
                token_idx += 1
    finally:
        if token_stream is not None:
            token_stream.close()

    return stats, token_path


def summarize_numeric(values: list[int]) -> dict[str, float | int]:
    if not values:
        return {"min": 0, "median": 0, "mean": 0.0, "p90": 0, "max": 0}
    ordered = sorted(values)
    p90_idx = min(len(ordered) - 1, math.ceil(len(ordered) * 0.9) - 1)
    return {
        "min": ordered[0],
        "median": statistics.median(ordered),
        "mean": round(statistics.mean(ordered), 2),
        "p90": ordered[p90_idx],
        "max": ordered[-1],
    }


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FloorPlanCAD primitive-token v0 manifests.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/tokens/floorplancad_v0"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/next_steps_2026-09-01"))
    parser.add_argument("--window-size", type=int, default=DEFAULT_WINDOW_SIZE)
    parser.add_argument("--limit-per-split", type=int, default=0, help="Debug limit; 0 means all files.")
    parser.add_argument(
        "--sample-token-files-per-split",
        type=int,
        default=0,
        help="Write token JSONL for the first N files per split; full manifest is still generated.",
    )
    parser.add_argument(
        "--write-full-token-jsonl",
        action="store_true",
        help="Write token JSONL for every file. This can create large local outputs and is not committed.",
    )
    args = parser.parse_args()

    roots = split_roots(args.root)
    missing = [str(path) for path in roots.values() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing FloorPlanCAD SVG directories: {missing}")
    if args.window_size <= 0:
        raise SystemExit("--window-size must be positive")

    file_stats: list[FileTokenStats] = []
    sample_token_files: list[dict[str, object]] = []
    split_file_counts: dict[str, int] = {}

    for split, split_root in roots.items():
        svg_files = sorted(split_root.glob("*.svg"))
        if args.limit_per_split:
            svg_files = svg_files[: args.limit_per_split]
        split_file_counts[split] = len(svg_files)
        for idx, svg_path in enumerate(svg_files, start=1):
            if idx % 500 == 0:
                print(f"[primitive-token] split={split} parsed={idx}/{len(svg_files)}", flush=True)
            should_write = args.write_full_token_jsonl or idx <= args.sample_token_files_per_split
            stats, token_path = inspect_svg(split, svg_path, should_write, args.out_dir / "tokens")
            file_stats.append(stats)
            if token_path is not None:
                sample_token_files.append(
                    {
                        "split": split,
                        "file": svg_path.name,
                        "token_file": str(token_path),
                        "sha256": sha256_file(token_path),
                        "token_count": stats.token_count,
                    }
                )

    manifest_rows: list[dict[str, object]] = []
    for stat in file_stats:
        row: dict[str, object] = {
            "split": stat.split,
            "file": stat.file,
            "token_count": stat.token_count,
            "semantic_token_count": stat.semantic_token_count,
            "unknown_semantic_token_count": stat.unknown_semantic_token_count,
            "class_count_nonzero": len(stat.class_ids),
            "window_size": args.window_size,
            "window_count": math.ceil(stat.token_count / args.window_size) if stat.token_count else 0,
            "text_element_count": stat.text_element_count,
            "viewbox_min_x": normalize_number(stat.viewbox_min_x, 3),
            "viewbox_min_y": normalize_number(stat.viewbox_min_y, 3),
            "viewbox_width": normalize_number(stat.viewbox_width, 3),
            "viewbox_height": normalize_number(stat.viewbox_height, 3),
        }
        for tag in sorted(SVG_GEOMETRY_TAGS):
            row[f"tag_{tag}"] = stat.tag_counts.get(tag, 0)
        manifest_rows.append(row)

    manifest_fields = [
        "split",
        "file",
        "token_count",
        "semantic_token_count",
        "unknown_semantic_token_count",
        "class_count_nonzero",
        "window_size",
        "window_count",
        "text_element_count",
        "viewbox_min_x",
        "viewbox_min_y",
        "viewbox_width",
        "viewbox_height",
        *[f"tag_{tag}" for tag in sorted(SVG_GEOMETRY_TAGS)],
    ]

    outputs_manifest = args.out_dir / "floorplancad_token_manifest_by_file.csv"
    report_manifest = args.report_dir / "floorplancad_token_manifest_by_file.csv"
    write_csv(outputs_manifest, manifest_rows, manifest_fields)
    write_csv(report_manifest, manifest_rows, manifest_fields)

    tag_totals: collections.Counter[str] = collections.Counter()
    command_totals: collections.Counter[str] = collections.Counter()
    token_counts_by_split: collections.Counter[str] = collections.Counter()
    semantic_counts_by_split: collections.Counter[str] = collections.Counter()
    windows_by_split: collections.Counter[str] = collections.Counter()
    for stat in file_stats:
        tag_totals.update(stat.tag_counts)
        command_totals.update(stat.path_command_counts)
        token_counts_by_split[stat.split] += stat.token_count
        semantic_counts_by_split[stat.split] += stat.semantic_token_count
        windows_by_split[stat.split] += math.ceil(stat.token_count / args.window_size) if stat.token_count else 0

    summary = {
        "generated_at": "2026-09-01",
        "token_version": TOKEN_VERSION,
        "source_root": str(args.root),
        "scope": "FloorPlanCAD public baseline split SVG files",
        "split_file_counts": split_file_counts,
        "window_size": args.window_size,
        "token_count_by_split": dict(token_counts_by_split),
        "semantic_token_count_by_split": dict(semantic_counts_by_split),
        "window_count_by_split": dict(windows_by_split),
        "total_tokens": sum(token_counts_by_split.values()),
        "total_semantic_tokens": sum(semantic_counts_by_split.values()),
        "file_level_token_count": summarize_numeric([stat.token_count for stat in file_stats]),
        "file_level_window_count": summarize_numeric(
            [math.ceil(stat.token_count / args.window_size) if stat.token_count else 0 for stat in file_stats]
        ),
        "global_tag_counts": dict(tag_totals.most_common()),
        "path_command_counts": dict(command_totals.most_common()),
        "manifest_sha256": sha256_file(outputs_manifest),
        "report_manifest_sha256": sha256_file(report_manifest),
        "sample_token_files": sample_token_files,
        "caveats": [
            "This is a primitive-token manifest and optional JSONL export, not a physical quantity or priced estimate.",
            "Path bbox is a dependency-free rough bbox based on numeric path coordinates; exact arc/Bezier envelopes are not recovered.",
            "Token JSONL files are local generated artifacts under outputs/ and should not be committed.",
        ],
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "floorplancad_token_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (args.report_dir / "floorplancad_token_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
