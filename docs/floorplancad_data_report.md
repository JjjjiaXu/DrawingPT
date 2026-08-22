# FloorPlanCAD data report

Generated locally on 2026-08-15.

## Download status

The public Google Drive IDs embedded in CADTransformer/SymPoint/GAT-CADNet were reachable from this machine.

Downloaded and extracted under `data/raw/FloorPlanCAD/`:

| Split | SVG files | Zip size |
|---|---:|---:|
| train | 6,965 | 84.9 MB |
| val | 810 | 10.2 MB |
| test | 3,827 | 40.4 MB |
| total | 11,602 | 135.5 MB |

This is the 11,602-file version used by public baseline scripts. The official website mentions a later 15,663-file update, so use the 11,602 version for baseline reproduction unless we intentionally switch all methods to the newer release.

## File structure

Each downloaded zip extracts into a nested split directory:

```text
data/raw/FloorPlanCAD/
  train/train/svg_gt/*.svg
  val/val/svg_gt/*.svg
  test/test/svg_gt/*.svg
```

## Annotation fields

SVG primitives carry:

- `semanticId`: class id
- `instanceId`: object instance id; `-1` appears for stuff/background-like primitives
- geometry fields such as `d`, `cx`, `cy`, `r`, `rx`, `ry`
- drawing style fields such as `stroke`, `fill`, `stroke-width`

In sampled SVGs, the main primitive tags are `path`, `circle`, and `ellipse`. I did not observe DWG-native block references in this SVG release, which matters for DrawingPT: FloorPlanCAD is vector, but not fully DWG-native.

## Per-split statistics

| Split | Files | Primitive median | Primitive mean | Primitive max | Instance median | Instance mean | Instance max |
|---|---:|---:|---:|---:|---:|---:|---:|
| train | 6,965 | 540 | 1,114.79 | 32,416 | 7 | 14.93 | 211 |
| val | 810 | 571 | 1,116.69 | 53,919 | 7 | 14.76 | 181 |
| test | 3,827 | 551 | 1,032.73 | 27,993 | 7 | 14.28 | 170 |

## Top semantic classes by primitive count

Across all splits, the heavy classes are wall, bed, row chairs, sink, toilet, parking spot, chair, stairs, wardrobe, doors, and windows. The distribution is highly imbalanced: rare classes include folding door, revolving door, rolling door, bay window, and opening symbol.

This confirms two practical points:

1. A baseline must report proper panoptic/instance metrics, not only primitive-level semantic accuracy.
2. DrawingPT should evaluate low-label regimes carefully because rare classes may disappear under small label fractions.

## Generated reports

- `outputs/reports/floorplancad_scan_all.json`
- `outputs/reports/floorplancad_train_stats.json`
- `outputs/reports/floorplancad_val_stats.json`
- `outputs/reports/floorplancad_test_stats.json`
- `outputs/reports/floorplancad_*_file_stats.csv`

