# FloorPlanCAD - 10-line note

1. FloorPlanCAD is the primary benchmark for DrawingPT.
2. It provides real-world architectural CAD drawings represented as SVG vector graphics.
3. The official site reports an updated release with 15,663 CAD drawings.
4. Each drawing includes SVG annotation fields, PNG renderings, and COCO visualization folders.
5. The task is panoptic symbol spotting: countable thing instances plus uncountable stuff semantics.
6. The original ICCV 2021 paper reports line-grained annotations for 30 object categories.
7. The kickoff document says our project should use it for the main evaluation curve.
8. What we need to inspect locally: primitive types, annotation attributes, split sizes, text availability, and layer-like fields.
9. Main limitation for DrawingPT: SVG may not retain all DWG-native structure such as block definitions/references.
10. Immediate next step: download data, run `scripts/scan_floorplancad.py`, and write a concrete data-format report.

