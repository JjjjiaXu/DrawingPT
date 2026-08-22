# DXF / DWG-to-vector toolchain report

Generated on 2026-08-22.

## Scope and discipline

- Current project stage uses only public datasets and synthetic/test drawings.
- Private/business drawings are out of scope until a data agreement exists.
- Raw DXF/DWG files belong under `data/raw/` or another ignored local data directory; do not commit them.
- This repo does not claim native DWG parsing yet. The safe path is DWG -> DXF conversion outside the repo, then DXF inspection with `ezdxf`.

## Current implementation

The local utility is:

```powershell
python scripts/inspect_dxf.py --input path\to\drawing.dxf --json-out outputs/reports/dxf_summary.json
```

The script uses `ezdxf` and records:

- entity type counts;
- top layers;
- top block references from `INSERT`;
- text examples from `TEXT` and `MTEXT`;
- preview geometry for common entities.

Supported geometry preview fields now include:

| DXF entity | Extracted fields |
|---|---|
| `LINE` | start, end |
| `ARC` | center, radius, start/end angles |
| `CIRCLE` | center, radius |
| `ELLIPSE` | center, major axis, ratio, start/end params |
| `LWPOLYLINE` / `POLYLINE` | closed flag and first points |
| `SPLINE` | degree and first control points |
| `INSERT` | block name, insertion point, scale, rotation |
| `TEXT` / `MTEXT` | text, insertion point, height, rotation |
| `DIMENSION` | dimension type and text field when present |

## What this confirms

For DXF files, the repo can extract the first-week fields needed by the kickoff checklist:

1. primitive/entity type;
2. geometry parameters;
3. layer-like attributes;
4. block references;
5. text annotations.

## What is not yet confirmed

- No private DWG has been touched.
- Native DWG parsing is not implemented here.
- A real public DXF sample should still be added to `data/raw/` locally and inspected before making quantitative claims about DWG coverage.
- DWG -> DXF conversion quality is an external dependency; candidate tools include AutoCAD export, ODA File Converter, LibreDWG, or other lab-approved converters.

## Next gate

Before using non-FloorPlanCAD drawings for pre-training, freeze a public DXF smoke sample and store:

- source URL or generation script;
- converter name/version if converted from DWG;
- `inspect_dxf.py` JSON summary hash;
- whether text, layers, block references, and dimensions survive conversion.
