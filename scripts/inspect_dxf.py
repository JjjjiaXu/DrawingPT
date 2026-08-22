from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import ezdxf


INTERESTING_TYPES = {
    "LINE",
    "ARC",
    "CIRCLE",
    "ELLIPSE",
    "LWPOLYLINE",
    "POLYLINE",
    "SPLINE",
    "INSERT",
    "TEXT",
    "MTEXT",
    "HATCH",
    "DIMENSION",
}


def vec_to_list(value) -> list[float] | str:
    """Convert ezdxf Vec2/Vec3-like values into JSON-friendly coordinates."""
    try:
        return [float(v) for v in value]
    except TypeError:
        return str(value)


def dxf_attr(entity, name: str, default=None):
    return getattr(entity.dxf, name, default)


def limited_points(points, limit: int = 12) -> list:
    out = []
    for idx, point in enumerate(points):
        if idx >= limit:
            break
        out.append(vec_to_list(point))
    return out


def entity_record(entity) -> dict[str, object]:
    dxftype = entity.dxftype()
    layer = dxf_attr(entity, "layer", "")
    record: dict[str, object] = {"type": dxftype, "layer": layer}

    if dxftype == "LINE":
        record["start"] = vec_to_list(dxf_attr(entity, "start", ()))
        record["end"] = vec_to_list(dxf_attr(entity, "end", ()))
    elif dxftype == "ARC":
        record["center"] = vec_to_list(dxf_attr(entity, "center", ()))
        record["radius"] = dxf_attr(entity, "radius", None)
        record["start_angle"] = dxf_attr(entity, "start_angle", None)
        record["end_angle"] = dxf_attr(entity, "end_angle", None)
    elif dxftype == "CIRCLE":
        record["center"] = vec_to_list(dxf_attr(entity, "center", ()))
        record["radius"] = dxf_attr(entity, "radius", None)
    elif dxftype == "ELLIPSE":
        record["center"] = vec_to_list(dxf_attr(entity, "center", ()))
        record["major_axis"] = vec_to_list(dxf_attr(entity, "major_axis", ()))
        record["ratio"] = dxf_attr(entity, "ratio", None)
        record["start_param"] = dxf_attr(entity, "start_param", None)
        record["end_param"] = dxf_attr(entity, "end_param", None)
    elif dxftype == "LWPOLYLINE":
        record["closed"] = bool(getattr(entity, "closed", False))
        record["points_preview"] = limited_points(entity.get_points())
    elif dxftype == "POLYLINE":
        record["closed"] = bool(getattr(entity, "is_closed", False))
        record["points_preview"] = limited_points(
            getattr(v.dxf, "location", ()) for v in entity.vertices
        )
    elif dxftype == "SPLINE":
        record["degree"] = dxf_attr(entity, "degree", None)
        record["control_points_preview"] = limited_points(getattr(entity, "control_points", []))
    elif dxftype == "INSERT":
        record["block"] = dxf_attr(entity, "name", "")
        record["insert"] = vec_to_list(dxf_attr(entity, "insert", ()))
        record["xscale"] = dxf_attr(entity, "xscale", 1.0)
        record["yscale"] = dxf_attr(entity, "yscale", 1.0)
        record["rotation"] = dxf_attr(entity, "rotation", 0.0)
    elif dxftype in {"TEXT", "MTEXT"}:
        record["text"] = getattr(entity, "plain_text", lambda: dxf_attr(entity, "text", ""))()
        record["insert"] = vec_to_list(dxf_attr(entity, "insert", ()))
        record["height"] = dxf_attr(entity, "height", dxf_attr(entity, "char_height", None))
        record["rotation"] = dxf_attr(entity, "rotation", 0.0)
    elif dxftype == "DIMENSION":
        record["dimension_type"] = dxf_attr(entity, "dimtype", None)
        record["text"] = dxf_attr(entity, "text", "")
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect primitive and layer statistics in a DXF file.")
    parser.add_argument("--input", required=True, type=Path, help="DXF file path.")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional path for JSON summary.")
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"DXF file does not exist: {args.input}")

    doc = ezdxf.readfile(args.input)
    modelspace = doc.modelspace()

    type_counts: collections.Counter[str] = collections.Counter()
    layer_counts: collections.Counter[str] = collections.Counter()
    block_counts: collections.Counter[str] = collections.Counter()
    text_examples: list[str] = []
    examples: list[dict[str, object]] = []

    for entity in modelspace:
        dxftype = entity.dxftype()
        type_counts[dxftype] += 1
        layer_counts[dxf_attr(entity, "layer", "")] += 1
        if dxftype == "INSERT":
            block_counts[dxf_attr(entity, "name", "")] += 1
        if dxftype in {"TEXT", "MTEXT"} and len(text_examples) < 20:
            text = getattr(entity, "plain_text", lambda: dxf_attr(entity, "text", ""))()
            if text:
                text_examples.append(str(text)[:120])
        if dxftype in INTERESTING_TYPES and len(examples) < 30:
            examples.append(entity_record(entity))

    summary = {
        "file": str(args.input),
        "type_counts": dict(type_counts.most_common()),
        "layer_counts_top50": dict(layer_counts.most_common(50)),
        "block_counts_top50": dict(block_counts.most_common(50)),
        "text_examples": text_examples,
        "entity_examples": examples,
    }

    text = json.dumps(summary, indent=2, ensure_ascii=False)
    print(text)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
