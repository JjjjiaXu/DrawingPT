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
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np


TOKEN_DATASET_VERSION = "drawingpt-v0-window-dataset-0.1"

PRIMITIVE_TYPE_TO_ID = {
    "path": 1,
    "circle": 2,
    "ellipse": 3,
    "line": 4,
    "polyline": 5,
    "polygon": 6,
    "rect": 7,
}
PAD_TYPE_ID = 0
MASK_TYPE_ID = max(PRIMITIVE_TYPE_TO_ID.values()) + 1
INPUT_TYPE_VOCAB_SIZE = MASK_TYPE_ID + 1
PREDICT_TYPE_VOCAB_SIZE = max(PRIMITIVE_TYPE_TO_ID.values()) + 1

FEATURE_NAMES = [
    "bbox_x0_norm",
    "bbox_y0_norm",
    "bbox_x1_norm",
    "bbox_y1_norm",
    "center_x_norm",
    "center_y_norm",
    "width_norm",
    "height_norm",
    "length_log",
    "area_log",
    "stroke_width_log",
    "has_fill",
    "has_stroke",
]

POINT_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
PATH_TOKEN_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


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


@dataclass(frozen=True)
class WindowRecord:
    split: str
    file: str
    svg_path: Path
    window_index: int
    start: int
    end: int
    token_count: int


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def attr_value(attrs: Dict[str, str], name: str) -> Optional[str]:
    target = name.lower()
    for key, value in attrs.items():
        if local_name(key).lower() == target:
            return value
    return None


def int_attr(attrs: Dict[str, str], name: str) -> Optional[int]:
    value = attr_value(attrs, name)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def float_attr(attrs: Dict[str, str], name: str) -> Optional[float]:
    value = attr_value(attrs, name)
    if value is None:
        return None
    match = POINT_RE.search(value)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def split_svg_root(root: Path, split: str) -> Path:
    candidates = [
        root / split / split / "svg_gt",  # Local raw FloorPlanCAD layout.
        root / "svg" / split,  # Server processed CADTransformer layout.
        root / split,  # Direct split layout.
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def parse_viewbox(root: ET.Element) -> Tuple[float, float, float, float]:
    viewbox = attr_value(root.attrib, "viewBox")
    if viewbox:
        values = [float(x) for x in POINT_RE.findall(viewbox)]
        if len(values) >= 4 and values[2] != 0 and values[3] != 0:
            return values[0], values[1], values[2], values[3]
    width = float_attr(root.attrib, "width") or 1.0
    height = float_attr(root.attrib, "height") or 1.0
    return 0.0, 0.0, width if width != 0 else 1.0, height if height != 0 else 1.0


def bounds_from_points(points: Iterable[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
    pts = list(points)
    if not pts:
        return None
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def path_bbox_rough(d: str) -> Optional[Tuple[float, float, float, float]]:
    values = [float(x) for x in POINT_RE.findall(d)]
    if len(values) < 2:
        return None
    return bounds_from_points(zip(values[0::2], values[1::2]))


def geometry_bbox(tag: str, attrs: Dict[str, str]) -> Optional[Tuple[float, float, float, float]]:
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


def distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def path_length_approx(d: str) -> float:
    tokens = PATH_TOKEN_RE.findall(d)
    i = 0
    cmd = ""
    current = (0.0, 0.0)
    start = (0.0, 0.0)
    total = 0.0

    def is_cmd(token: str) -> bool:
        return len(token) == 1 and token.isalpha()

    def take_number() -> Optional[float]:
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

        if op == "A":
            values = [take_number() for _ in range(7)]
            if any(v is None for v in values):
                break
            rx, ry, _rot, _large_arc, _sweep, x, y = [float(v) for v in values if v is not None]
            nxt = (x, y) if absolute else (current[0] + x, current[1] + y)
            chord = distance(current, nxt)
            radius_proxy = max(abs(rx), abs(ry), chord / 2)
            total += max(chord, min(math.pi * radius_proxy, 2 * chord if chord else 0.0))
            current = nxt
            continue

        # Curves and less common commands are approximated by the rough bbox
        # diagonal. FloorPlanCAD is dominated by M/L/A path commands.
        break

    if total == 0.0:
        bbox = path_bbox_rough(d)
        if bbox is not None:
            return math.hypot(bbox[2] - bbox[0], bbox[3] - bbox[1])
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


def geometry_length(tag: str, attrs: Dict[str, str]) -> float:
    if tag == "path":
        return path_length_approx(attrs.get("d", ""))
    if tag == "circle":
        return 2 * math.pi * (float_attr(attrs, "r") or 0.0)
    if tag == "ellipse":
        rx = float_attr(attrs, "rx") or 0.0
        ry = float_attr(attrs, "ry") or 0.0
        if rx <= 0 or ry <= 0:
            return 0.0
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


def safe_norm(value: float, origin: float, scale: float) -> float:
    if not math.isfinite(value) or scale == 0:
        return 0.0
    result = (value - origin) / scale
    if not math.isfinite(result):
        return 0.0
    return float(max(-10.0, min(10.0, result)))


def primitive_features(tag: str, attrs: Dict[str, str], viewbox: Tuple[float, float, float, float]) -> Tuple[int, np.ndarray, int, int]:
    min_x, min_y, width, height = viewbox
    diag = math.hypot(width, height) or 1.0
    bbox = geometry_bbox(tag, attrs)
    if bbox is None:
        x0 = y0 = x1 = y1 = cx = cy = w = h = area = 0.0
    else:
        bx0, by0, bx1, by1 = bbox
        x0 = safe_norm(bx0, min_x, width)
        y0 = safe_norm(by0, min_y, height)
        x1 = safe_norm(bx1, min_x, width)
        y1 = safe_norm(by1, min_y, height)
        raw_w = max(0.0, bx1 - bx0)
        raw_h = max(0.0, by1 - by0)
        cx = safe_norm(bx0 + raw_w / 2, min_x, width)
        cy = safe_norm(by0 + raw_h / 2, min_y, height)
        w = max(0.0, min(10.0, raw_w / width if width else 0.0))
        h = max(0.0, min(10.0, raw_h / height if height else 0.0))
        area = raw_w * raw_h

    length = geometry_length(tag, attrs)
    stroke_width = float_attr(attrs, "stroke-width") or 0.0
    fill = attr_value(attrs, "fill")
    stroke = attr_value(attrs, "stroke")
    class_id = int_attr(attrs, "semanticId")
    instance_id = int_attr(attrs, "instanceId")
    type_id = PRIMITIVE_TYPE_TO_ID[tag]

    values = np.array(
        [
            x0,
            y0,
            x1,
            y1,
            cx,
            cy,
            w,
            h,
            math.log1p(max(0.0, length / diag)),
            math.log1p(max(0.0, area / (width * height if width and height else 1.0))),
            math.log1p(max(0.0, stroke_width)),
            1.0 if fill and fill.lower() != "none" else 0.0,
            1.0 if stroke and stroke.lower() != "none" else 0.0,
        ],
        dtype=np.float32,
    )
    values[~np.isfinite(values)] = 0.0
    return type_id, values, class_id or 0, instance_id if instance_id is not None else -1


def parse_svg_tokens(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    root = ET.parse(str(path)).getroot()
    viewbox = parse_viewbox(root)
    type_ids: List[int] = []
    features: List[np.ndarray] = []
    semantic_labels: List[int] = []
    instance_ids: List[int] = []

    for elem in root.iter():
        tag = local_name(elem.tag)
        if tag not in PRIMITIVE_TYPE_TO_ID:
            continue
        type_id, feature, semantic_id, instance_id = primitive_features(tag, elem.attrib, viewbox)
        type_ids.append(type_id)
        features.append(feature)
        semantic_labels.append(semantic_id)
        instance_ids.append(instance_id)

    if not type_ids:
        return (
            np.zeros((0,), dtype=np.int64),
            np.zeros((0, len(FEATURE_NAMES)), dtype=np.float32),
            np.zeros((0,), dtype=np.int64),
            np.zeros((0,), dtype=np.int64),
        )

    return (
        np.asarray(type_ids, dtype=np.int64),
        np.stack(features).astype(np.float32),
        np.asarray(semantic_labels, dtype=np.int64),
        np.asarray(instance_ids, dtype=np.int64),
    )


def read_label_list(path: Optional[Path]) -> Optional[set]:
    if path is None:
        return None
    allowed = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip().replace("\\", "/")
        if stripped:
            allowed.add(Path(stripped).name)
    return allowed


def build_window_records(
    root: Path,
    manifest_path: Path,
    split: str,
    window_size: int,
    label_list_path: Optional[Path] = None,
    limit_files: int = 0,
    limit_windows: int = 0,
) -> List[WindowRecord]:
    allowed = read_label_list(label_list_path)
    records: List[WindowRecord] = []
    seen_files = 0
    with manifest_path.open("r", newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if row["split"] != split:
                continue
            file_name = row["file"]
            if allowed is not None and file_name not in allowed:
                continue
            if limit_files and seen_files >= limit_files:
                break
            seen_files += 1
            token_count = int(row["token_count"])
            window_count = int(math.ceil(float(token_count) / float(window_size))) if token_count else 0
            svg_path = split_svg_root(root, split) / file_name
            for window_index in range(window_count):
                start = window_index * window_size
                end = min(token_count, start + window_size)
                records.append(WindowRecord(split, file_name, svg_path, window_index, start, end, token_count))
                if limit_windows and len(records) >= limit_windows:
                    return records
    return records


class FloorPlanCADPrimitiveDataset(object):
    """Primitive-window dataset for DrawingPT v0.

    This class deliberately avoids inheriting from torch Dataset so the same
    file can be inspected on machines without torch. PyTorch DataLoader can
    still consume it because it implements __len__ and __getitem__.
    """

    def __init__(
        self,
        root: Path,
        manifest_path: Path,
        split: str,
        window_size: int = 2048,
        label_list_path: Optional[Path] = None,
        limit_files: int = 0,
        limit_windows: int = 0,
    ) -> None:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        self.root = root
        self.manifest_path = manifest_path
        self.split = split
        self.window_size = window_size
        self.label_list_path = label_list_path
        self.records = build_window_records(
            root=root,
            manifest_path=manifest_path,
            split=split,
            window_size=window_size,
            label_list_path=label_list_path,
            limit_files=limit_files,
            limit_windows=limit_windows,
        )
        self._cache_file: Optional[Path] = None
        self._cache_tokens: Optional[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = None

    @property
    def feature_dim(self) -> int:
        return len(FEATURE_NAMES)

    def __len__(self) -> int:
        return len(self.records)

    def _load_tokens(self, path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if self._cache_file == path and self._cache_tokens is not None:
            return self._cache_tokens
        tokens = parse_svg_tokens(path)
        self._cache_file = path
        self._cache_tokens = tokens
        return tokens

    def __getitem__(self, index: int) -> Dict[str, object]:
        record = self.records[index]
        if not record.svg_path.exists():
            raise FileNotFoundError(str(record.svg_path))

        type_ids_all, features_all, semantic_all, instance_all = self._load_tokens(record.svg_path)
        type_ids = type_ids_all[record.start : record.end]
        features = features_all[record.start : record.end]
        semantic_labels = semantic_all[record.start : record.end]
        instance_ids = instance_all[record.start : record.end]

        valid = len(type_ids)
        padded_type_ids = np.zeros((self.window_size,), dtype=np.int64)
        padded_features = np.zeros((self.window_size, self.feature_dim), dtype=np.float32)
        padded_semantic = np.full((self.window_size,), -100, dtype=np.int64)
        padded_instance = np.full((self.window_size,), -1, dtype=np.int64)
        attention_mask = np.zeros((self.window_size,), dtype=np.bool_)

        if valid:
            padded_type_ids[:valid] = type_ids
            padded_features[:valid] = features
            padded_semantic[:valid] = semantic_labels
            padded_instance[:valid] = instance_ids
            attention_mask[:valid] = True

        return {
            "features": padded_features,
            "type_ids": padded_type_ids,
            "semantic_labels": padded_semantic,
            "instance_ids": padded_instance,
            "attention_mask": attention_mask,
            "split": record.split,
            "file": record.file,
            "window_index": record.window_index,
            "start": record.start,
            "end": record.end,
            "token_count": record.token_count,
        }


def describe(values: Sequence[int]) -> Dict[str, object]:
    if not values:
        return {"min": 0, "median": 0, "mean": 0.0, "p90": 0, "max": 0}
    ordered = sorted(int(v) for v in values)
    p90_idx = min(len(ordered) - 1, int(math.ceil(len(ordered) * 0.9)) - 1)
    return {
        "min": ordered[0],
        "median": statistics.median(ordered),
        "mean": round(statistics.mean(ordered), 2),
        "p90": ordered[p90_idx],
        "max": ordered[-1],
    }


def summarize_dataset(dataset: FloorPlanCADPrimitiveDataset, max_items: int) -> Dict[str, object]:
    type_counts: collections.Counter = collections.Counter()
    class_counts: collections.Counter = collections.Counter()
    valid_counts: List[int] = []
    finite_feature_windows = 0
    inspected = min(len(dataset), max_items)

    for idx in range(inspected):
        item = dataset[idx]
        mask = item["attention_mask"]
        type_ids = item["type_ids"][mask]
        labels = item["semantic_labels"][mask]
        features = item["features"][mask]
        valid_counts.append(int(mask.sum()))
        type_counts.update(int(x) for x in type_ids.tolist())
        class_counts.update(int(x) for x in labels.tolist() if int(x) > 0)
        if np.isfinite(features).all():
            finite_feature_windows += 1

    id_to_type = {value: key for key, value in PRIMITIVE_TYPE_TO_ID.items()}
    summary = {
        "dataset_version": TOKEN_DATASET_VERSION,
        "split": dataset.split,
        "window_size": dataset.window_size,
        "dataset_windows": len(dataset),
        "inspected_windows": inspected,
        "feature_dim": dataset.feature_dim,
        "feature_names": FEATURE_NAMES,
        "valid_tokens_per_inspected_window": describe(valid_counts),
        "finite_feature_windows": finite_feature_windows,
        "type_counts": {id_to_type.get(key, str(key)): value for key, value in sorted(type_counts.items())},
        "top_semantic_classes": [
            {"class_id": key, "class_name": CLASS_NAMES.get(key, "<unknown>"), "count": value}
            for key, value in class_counts.most_common(10)
        ],
        "manifest": str(dataset.manifest_path),
        "manifest_sha256": sha256_file(dataset.manifest_path),
        "label_list": str(dataset.label_list_path) if dataset.label_list_path else None,
        "label_list_sha256": sha256_file(dataset.label_list_path) if dataset.label_list_path else None,
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-check the DrawingPT v0 primitive-window dataset.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv"),
    )
    parser.add_argument("--split", choices=["train", "val", "test"], default="train")
    parser.add_argument("--label-list", type=Path, default=None)
    parser.add_argument("--window-size", type=int, default=2048)
    parser.add_argument("--limit-files", type=int, default=0)
    parser.add_argument("--limit-windows", type=int, default=0)
    parser.add_argument("--inspect-windows", type=int, default=8)
    parser.add_argument("--summary-out", type=Path, default=None)
    args = parser.parse_args()

    dataset = FloorPlanCADPrimitiveDataset(
        root=args.root,
        manifest_path=args.manifest,
        split=args.split,
        window_size=args.window_size,
        label_list_path=args.label_list,
        limit_files=args.limit_files,
        limit_windows=args.limit_windows,
    )
    summary = summarize_dataset(dataset, max_items=args.inspect_windows)
    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
