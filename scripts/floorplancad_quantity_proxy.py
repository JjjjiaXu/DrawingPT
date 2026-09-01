from __future__ import annotations

import argparse
import collections
import csv
import json
import math
import re
import statistics
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
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


CLASS_ROLES = {
    1: "开口/门窗",
    2: "开口/门窗",
    3: "开口/门窗",
    4: "开口/门窗",
    5: "开口/门窗",
    6: "开口/门窗",
    7: "开口/门窗",
    8: "开口/门窗",
    9: "开口/门窗",
    10: "开口/门窗",
    16: "柜体/固定家具",
    17: "柜体/固定家具",
    18: "厨卫/设备点位",
    19: "厨卫/设备点位",
    20: "厨卫/设备点位",
    21: "厨卫/设备点位",
    22: "厨卫/设备点位",
    23: "厨卫/设备点位",
    24: "厨卫/设备点位",
    25: "厨卫/设备点位",
    26: "厨卫/设备点位",
    27: "厨卫/设备点位",
    28: "垂直交通",
    29: "垂直交通",
    30: "垂直交通",
    32: "车位",
    33: "墙体/围护",
    34: "墙体/围护",
    35: "墙体/围护",
    11: "可选 FF&E",
    12: "可选 FF&E",
    13: "可选 FF&E",
    14: "可选 FF&E",
    15: "可选 FF&E",
    31: "可选 FF&E",
}


CORE_CLASS_IDS = {
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    32,
    33,
    34,
    35,
}

LENGTH_CLASS_IDS = {
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    28,
    29,
    30,
    32,
    33,
    34,
    35,
}


SVG_GEOMETRY_TAGS = {"path", "circle", "ellipse", "line", "polyline", "polygon", "rect"}
PATH_TOKEN_RE = re.compile(
    r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?"
)
POINT_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


@dataclass
class ClassStat:
    split: str
    class_id: int
    class_name: str
    role: str
    semantic_elements: int = 0
    tagged_geometry_elements: int = 0
    approximate_svg_length: float = 0.0
    files: set[str] = field(default_factory=set)
    instances: set[tuple[str, str]] = field(default_factory=set)


@dataclass
class FileStat:
    split: str
    file: str
    semantic_elements: int = 0
    core_semantic_elements: int = 0
    core_instances: set[tuple[int, str]] = field(default_factory=set)
    approximate_svg_length: float = 0.0
    class_semantic_elements: collections.Counter[int] = field(default_factory=collections.Counter)
    class_instances: dict[int, set[str]] = field(default_factory=lambda: collections.defaultdict(set))
    class_approximate_svg_length: collections.Counter[int] = field(default_factory=collections.Counter)


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


def float_attr(attrs: dict[str, str], name: str) -> float | None:
    for key, value in attrs.items():
        if local_name(key).lower() == name.lower():
            try:
                return float(value)
            except ValueError:
                return None
    return None


def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def path_length_approx(d: str) -> float:
    """Approximate SVG path length without external dependencies.

    FloorPlanCAD paths are dominated by M/L/A commands. Lines are exact here;
    Bezier curves are approximated by control-polygon length; arcs are
    conservatively approximated by endpoint chord length. The result is a
    stable proxy in SVG coordinate units, not a physical quantity.
    """

    command_letters = re.findall(r"[A-Za-z]", d)
    if command_letters and set(command_letters) <= {"M", "L"}:
        values = [float(x) for x in POINT_RE.findall(d)]
        pts = list(zip(values[0::2], values[1::2]))
        if len(pts) >= 2:
            return sum(distance(a, b) for a, b in zip(pts, pts[1:]))

    tokens = PATH_TOKEN_RE.findall(d)
    i = 0
    cmd = ""
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    total = 0.0

    def is_cmd(token: str) -> bool:
        return len(token) == 1 and token.isalpha()

    def take_number() -> float | None:
        nonlocal i
        if i >= len(tokens) or is_cmd(tokens[i]):
            return None
        value = float(tokens[i])
        i += 1
        return value

    while i < len(tokens):
        if is_cmd(tokens[i]):
            cmd = tokens[i]
            i += 1
        if not cmd:
            break

        absolute = cmd.isupper()
        op = cmd.upper()

        if op == "Z":
            total += distance(current, start)
            current = start
            cmd = ""
            continue

        if op == "M":
            x = take_number()
            y = take_number()
            if x is None or y is None:
                break
            current = (x, y) if absolute else (current[0] + x, current[1] + y)
            start = current
            cmd = "L" if absolute else "l"
            continue

        if op == "L":
            x = take_number()
            y = take_number()
            if x is None or y is None:
                break
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            total += distance(current, nxt)
            current = nxt
            continue

        if op == "H":
            x = take_number()
            if x is None:
                break
            nxt = (x, current[1]) if absolute else (current[0] + x, current[1])
            total += distance(current, nxt)
            current = nxt
            continue

        if op == "V":
            y = take_number()
            if y is None:
                break
            nxt = (current[0], y) if absolute else (current[0], current[1] + y)
            total += distance(current, nxt)
            current = nxt
            continue

        if op == "C":
            values = [take_number() for _ in range(6)]
            if any(v is None for v in values):
                break
            x1, y1, x2, y2, x, y = [float(v) for v in values if v is not None]
            p1 = (x1, y1) if absolute else (current[0] + x1, current[1] + y1)
            p2 = (x2, y2) if absolute else (current[0] + x2, current[1] + y2)
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            total += distance(current, p1) + distance(p1, p2) + distance(p2, nxt)
            current = nxt
            continue

        if op in {"S", "Q"}:
            values = [take_number() for _ in range(4)]
            if any(v is None for v in values):
                break
            x1, y1, x, y = [float(v) for v in values if v is not None]
            p1 = (x1, y1) if absolute else (current[0] + x1, current[1] + y1)
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            total += distance(current, p1) + distance(p1, nxt)
            current = nxt
            continue

        if op == "T":
            x = take_number()
            y = take_number()
            if x is None or y is None:
                break
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            total += distance(current, nxt)
            current = nxt
            continue

        if op == "A":
            values = [take_number() for _ in range(7)]
            if any(v is None for v in values):
                break
            rx, ry, _rot, _large_arc, _sweep, x, y = [float(v) for v in values if v is not None]
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            chord = distance(current, nxt)
            radius_proxy = max(abs(rx), abs(ry), chord / 2)
            # Use a conservative half-circumference cap when chord is too small.
            total += max(chord, min(math.pi * radius_proxy, 2 * chord if chord else 0.0))
            current = nxt
            continue

        # Unknown command: stop rather than silently inventing a quantity.
        break

    return total


def points_length(points: str, closed: bool) -> float:
    values = [float(x) for x in POINT_RE.findall(points)]
    pts = list(zip(values[0::2], values[1::2]))
    if len(pts) < 2:
        return 0.0
    total = sum(distance(a, b) for a, b in zip(pts, pts[1:]))
    if closed:
        total += distance(pts[-1], pts[0])
    return total


def geometry_length(tag: str, attrs: dict[str, str]) -> float:
    if tag == "path":
        return path_length_approx(attrs.get("d", ""))
    if tag == "circle":
        r = float_attr(attrs, "r") or 0.0
        return 2 * math.pi * r
    if tag == "ellipse":
        rx = float_attr(attrs, "rx") or 0.0
        ry = float_attr(attrs, "ry") or 0.0
        if rx <= 0 or ry <= 0:
            return 0.0
        # Ramanujan approximation.
        h = ((rx - ry) ** 2) / ((rx + ry) ** 2)
        return math.pi * (rx + ry) * (1 + (3 * h) / (10 + math.sqrt(4 - 3 * h)))
    if tag == "line":
        x1 = float_attr(attrs, "x1") or 0.0
        y1 = float_attr(attrs, "y1") or 0.0
        x2 = float_attr(attrs, "x2") or 0.0
        y2 = float_attr(attrs, "y2") or 0.0
        return math.hypot(x1 - x2, y1 - y2)
    if tag == "polyline":
        return points_length(attrs.get("points", ""), closed=False)
    if tag == "polygon":
        return points_length(attrs.get("points", ""), closed=True)
    if tag == "rect":
        width = float_attr(attrs, "width") or 0.0
        height = float_attr(attrs, "height") or 0.0
        return 2 * (width + height)
    return 0.0


def split_roots(root: Path) -> dict[str, Path]:
    return {
        "train": root / "train" / "train" / "svg_gt",
        "val": root / "val" / "val" / "svg_gt",
        "test": root / "test" / "test" / "svg_gt",
    }


def inspect_file(split: str, path: Path, class_stats: dict[tuple[str, int], ClassStat]) -> FileStat:
    file_stat = FileStat(split=split, file=path.name)
    root = ET.parse(path).getroot()

    for elem in root.iter():
        tag = local_name(elem.tag)
        attrs = elem.attrib
        class_id = int_attr(attrs, "semanticId")
        if class_id is None:
            continue

        class_name = CLASS_NAMES.get(class_id, "<unknown>")
        role = CLASS_ROLES.get(class_id, "其他")
        key = (split, class_id)
        if key not in class_stats:
            class_stats[key] = ClassStat(split=split, class_id=class_id, class_name=class_name, role=role)
        stat = class_stats[key]
        stat.semantic_elements += 1
        stat.files.add(path.name)
        file_stat.semantic_elements += 1
        file_stat.class_semantic_elements[class_id] += 1
        if class_id in CORE_CLASS_IDS:
            file_stat.core_semantic_elements += 1

        instance_id = int_attr(attrs, "instanceId")
        if instance_id is not None and instance_id >= 0:
            instance_key = (path.name, str(instance_id))
            stat.instances.add(instance_key)
            file_stat.class_instances[class_id].add(str(instance_id))
            if class_id in CORE_CLASS_IDS:
                file_stat.core_instances.add((class_id, str(instance_id)))

        if class_id in LENGTH_CLASS_IDS and tag in SVG_GEOMETRY_TAGS:
            length = geometry_length(tag, attrs)
            stat.tagged_geometry_elements += 1
            stat.approximate_svg_length += length
            file_stat.class_approximate_svg_length[class_id] += length
            if class_id in CORE_CLASS_IDS:
                file_stat.approximate_svg_length += length

    return file_stat


def summarize_file_counts(values: list[int]) -> dict[str, float | int]:
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


def count_instances(stat: FileStat, class_ids: set[int]) -> int:
    return sum(len(stat.class_instances.get(class_id, set())) for class_id in class_ids)


def count_elements(stat: FileStat, class_ids: set[int]) -> int:
    return sum(stat.class_semantic_elements.get(class_id, 0) for class_id in class_ids)


def length_proxy(stat: FileStat, class_ids: set[int]) -> float:
    return sum(stat.class_approximate_svg_length.get(class_id, 0.0) for class_id in class_ids)


def pseudo_boq_row(stat: FileStat) -> dict[str, object]:
    door_ids = {1, 2, 3, 4, 5, 6}
    window_ids = {7, 8, 9}
    opening_ids = door_ids | window_ids | {10}
    sanitary_ids = {19, 22, 23, 24, 25, 26, 27}
    kitchen_ids = {18, 20}
    vertical_ids = {28, 29, 30}
    wall_ids = {33, 34, 35}
    ffe_ids = {11, 12, 13, 14, 15, 31}

    return {
        "split": stat.split,
        "file": stat.file,
        "semantic_elements": stat.semantic_elements,
        "core_semantic_elements": stat.core_semantic_elements,
        "core_instance_count_nonnegative": len(stat.core_instances),
        "core_approx_svg_length_units": round(stat.approximate_svg_length, 3),
        "door_instance_count": count_instances(stat, door_ids),
        "window_instance_count": count_instances(stat, window_ids),
        "opening_symbol_instance_count": count_instances(stat, {10}),
        "door_window_opening_instance_count": count_instances(stat, opening_ids),
        "wall_semantic_elements": count_elements(stat, {33}),
        "wall_length_proxy_units": round(length_proxy(stat, {33}), 3),
        "curtain_wall_semantic_elements": count_elements(stat, {34}),
        "curtain_wall_length_proxy_units": round(length_proxy(stat, {34}), 3),
        "railing_semantic_elements": count_elements(stat, {35}),
        "railing_length_proxy_units": round(length_proxy(stat, {35}), 3),
        "stairs_instance_count": count_instances(stat, {28}),
        "elevator_instance_count": count_instances(stat, {29}),
        "escalator_instance_count": count_instances(stat, {30}),
        "vertical_transport_instance_count": count_instances(stat, vertical_ids),
        "sanitary_fixture_instance_count": count_instances(stat, sanitary_ids),
        "kitchen_equipment_instance_count": count_instances(stat, kitchen_ids),
        "hvac_instance_count": count_instances(stat, {21}),
        "cabinet_instance_count": count_instances(stat, {16, 17}),
        "parking_spot_semantic_elements": count_elements(stat, {32}),
        "parking_spot_length_proxy_units": round(length_proxy(stat, {32}), 3),
        "ffe_instance_count": count_instances(stat, ffe_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Create FloorPlanCAD quantity-takeoff proxy summaries.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument("--out-dir", type=Path, default=Path("outputs/reports"))
    parser.add_argument("--report-dir", type=Path, default=Path("reports/next_steps_2026-09-01"))
    parser.add_argument("--limit-per-split", type=int, default=0, help="Optional debug limit; 0 means all files.")
    args = parser.parse_args()

    roots = split_roots(args.root)
    missing = [str(path) for path in roots.values() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing FloorPlanCAD SVG directories: {missing}")

    class_stats: dict[tuple[str, int], ClassStat] = {}
    file_stats: list[FileStat] = []
    split_file_counts: dict[str, int] = {}

    for split, split_root in roots.items():
        svg_files = sorted(split_root.glob("*.svg"))
        if args.limit_per_split:
            svg_files = svg_files[: args.limit_per_split]
        split_file_counts[split] = len(svg_files)
        for idx, svg_path in enumerate(svg_files, start=1):
            if idx % 500 == 0:
                print(f"[quantity-proxy] split={split} parsed={idx}/{len(svg_files)}", flush=True)
            file_stats.append(inspect_file(split, svg_path, class_stats))

    by_class_rows: list[dict[str, object]] = []
    for (split, class_id), stat in sorted(class_stats.items()):
        by_class_rows.append(
            {
                "split": split,
                "class_id": class_id,
                "class_name": stat.class_name,
                "role": stat.role,
                "semantic_elements": stat.semantic_elements,
                "instance_count_nonnegative": len(stat.instances),
                "files_with_class": len(stat.files),
                "share_of_split_files": round(len(stat.files) / max(split_file_counts[split], 1), 6),
                "tagged_geometry_elements": stat.tagged_geometry_elements,
                "approx_svg_length_units": round(stat.approximate_svg_length, 3),
            }
        )

    group_acc: dict[tuple[str, str], dict[str, object]] = {}
    for row in by_class_rows:
        key = (str(row["split"]), str(row["role"]))
        if key not in group_acc:
            group_acc[key] = {
                "split": row["split"],
                "role": row["role"],
                "semantic_elements": 0,
                "instance_count_nonnegative": 0,
                "files_with_any_role": set(),
                "approx_svg_length_units": 0.0,
            }
        group = group_acc[key]
        group["semantic_elements"] = int(group["semantic_elements"]) + int(row["semantic_elements"])
        group["instance_count_nonnegative"] = int(group["instance_count_nonnegative"]) + int(
            row["instance_count_nonnegative"]
        )
        group["approx_svg_length_units"] = float(group["approx_svg_length_units"]) + float(
            row["approx_svg_length_units"]
        )

    # File coverage by role needs a second pass over class stats to avoid
    # over-counting files that contain several classes in the same role.
    role_files: dict[tuple[str, str], set[str]] = collections.defaultdict(set)
    for (_split, _class_id), stat in class_stats.items():
        role_files[(stat.split, stat.role)].update(stat.files)

    group_rows: list[dict[str, object]] = []
    for key, group in sorted(group_acc.items()):
        split, role = key
        files = role_files[key]
        group_rows.append(
            {
                "split": split,
                "role": role,
                "semantic_elements": group["semantic_elements"],
                "instance_count_nonnegative": group["instance_count_nonnegative"],
                "files_with_any_role": len(files),
                "share_of_split_files": round(len(files) / max(split_file_counts[split], 1), 6),
                "approx_svg_length_units": round(float(group["approx_svg_length_units"]), 3),
            }
        )

    file_rows = [
        {
            "split": stat.split,
            "file": stat.file,
            "semantic_elements": stat.semantic_elements,
            "core_semantic_elements": stat.core_semantic_elements,
            "core_instance_count_nonnegative": len(stat.core_instances),
            "core_approx_svg_length_units": round(stat.approximate_svg_length, 3),
        }
        for stat in file_stats
    ]
    pseudo_boq_rows = [pseudo_boq_row(stat) for stat in file_stats]

    write_csv(
        args.out_dir / "floorplancad_quantity_proxy_by_class.csv",
        by_class_rows,
        [
            "split",
            "class_id",
            "class_name",
            "role",
            "semantic_elements",
            "instance_count_nonnegative",
            "files_with_class",
            "share_of_split_files",
            "tagged_geometry_elements",
            "approx_svg_length_units",
        ],
    )
    write_csv(
        args.out_dir / "floorplancad_quantity_proxy_by_role.csv",
        group_rows,
        [
            "split",
            "role",
            "semantic_elements",
            "instance_count_nonnegative",
            "files_with_any_role",
            "share_of_split_files",
            "approx_svg_length_units",
        ],
    )
    write_csv(
        args.out_dir / "floorplancad_quantity_proxy_by_file.csv",
        file_rows,
        [
            "split",
            "file",
            "semantic_elements",
            "core_semantic_elements",
            "core_instance_count_nonnegative",
            "core_approx_svg_length_units",
        ],
    )
    pseudo_boq_fields = [
        "split",
        "file",
        "semantic_elements",
        "core_semantic_elements",
        "core_instance_count_nonnegative",
        "core_approx_svg_length_units",
        "door_instance_count",
        "window_instance_count",
        "opening_symbol_instance_count",
        "door_window_opening_instance_count",
        "wall_semantic_elements",
        "wall_length_proxy_units",
        "curtain_wall_semantic_elements",
        "curtain_wall_length_proxy_units",
        "railing_semantic_elements",
        "railing_length_proxy_units",
        "stairs_instance_count",
        "elevator_instance_count",
        "escalator_instance_count",
        "vertical_transport_instance_count",
        "sanitary_fixture_instance_count",
        "kitchen_equipment_instance_count",
        "hvac_instance_count",
        "cabinet_instance_count",
        "parking_spot_semantic_elements",
        "parking_spot_length_proxy_units",
        "ffe_instance_count",
    ]
    write_csv(
        args.out_dir / "floorplancad_pseudo_boq_by_file.csv",
        pseudo_boq_rows,
        pseudo_boq_fields,
    )

    # Commit only compact summaries under reports/. The full by-file table stays
    # in outputs/ because it is larger and mainly for local audit.
    report_dir = args.report_dir
    write_csv(
        report_dir / "floorplancad_quantity_proxy_by_class.csv",
        by_class_rows,
        [
            "split",
            "class_id",
            "class_name",
            "role",
            "semantic_elements",
            "instance_count_nonnegative",
            "files_with_class",
            "share_of_split_files",
            "tagged_geometry_elements",
            "approx_svg_length_units",
        ],
    )
    write_csv(
        report_dir / "floorplancad_quantity_proxy_by_role.csv",
        group_rows,
        [
            "split",
            "role",
            "semantic_elements",
            "instance_count_nonnegative",
            "files_with_any_role",
            "share_of_split_files",
            "approx_svg_length_units",
        ],
    )
    write_csv(
        report_dir / "floorplancad_pseudo_boq_by_file.csv",
        pseudo_boq_rows,
        pseudo_boq_fields,
    )

    summary = {
        "generated_at": "2026-09-01",
        "source_root": str(args.root),
        "scope": "FloorPlanCAD public 11,602 SVG baseline split",
        "split_file_counts": split_file_counts,
        "length_unit_warning": (
            "approx_svg_length_units is a geometry proxy in SVG coordinate units. "
            "It is not meters, square meters, or a priced quantity."
        ),
        "pseudo_boq_fields": {
            "door/window/opening/stairs/elevator/equipment/cabinet": "non-negative instanceId count by semantic class group",
            "wall/curtain_wall/railing/parking_length_proxy_units": "approximate SVG geometry length by semantic class",
            "parking_spot_semantic_elements": "semantic primitive count; FloorPlanCAD parking instanceId is not reliable for count",
        },
        "file_level_core_semantic_elements": summarize_file_counts(
            [stat.core_semantic_elements for stat in file_stats]
        ),
        "file_level_core_instance_count_nonnegative": summarize_file_counts(
            [len(stat.core_instances) for stat in file_stats]
        ),
        "file_level_core_approx_svg_length_units": summarize_file_counts(
            [round(stat.approximate_svg_length) for stat in file_stats]
        ),
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "floorplancad_quantity_proxy_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (report_dir / "floorplancad_quantity_proxy_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
