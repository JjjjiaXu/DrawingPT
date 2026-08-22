# DrawingPT v0 design draft

## One-sentence hypothesis

A small vector-native self-supervised model can learn reusable representations for 2D engineering drawings by predicting rasterized spatial occupancy from precise vector primitives and their structural relations.

## Input

Primitive stream:

- line: endpoints, length, angle, layer, stroke/color if available
- arc/circle/ellipse: center, radius/radii, angle range, layer
- polyline/path: sampled control or vertex sequence plus aggregate geometry
- block reference: insertion point, scale, rotation, block id/name, layer

Annotation/text stream:

- text content embedding
- insertion point / bounding box
- rotation / size
- layer and nearest primitives
- optional OCR-normalized numeric/unit features for dimensions

## Structural priors

Candidate attention biases:

- spatial adjacency: nearest neighbors, intersections, containment, overlap
- block hierarchy: primitives belonging to the same block definition or block reference
- layer relation: same layer or related layer prefix
- text binding: nearest text to primitive group, callout arrows, dimension lines

## Self-supervised objective

Start simple:

- input: vector primitives and structural graph
- target: local raster rendering around each primitive or drawing window
- loss: binary occupancy / distance-transform reconstruction / masked primitive reconstruction

Potential variants:

- masked primitive modeling: hide parameters and predict them from context
- vector-to-raster contrastive alignment: primitive/window embedding aligns with rendered crop embedding
- text-geometry binding: predict whether a text item belongs to a primitive group

## Downstream tasks

Primary:

- FloorPlanCAD panoptic symbol spotting.

Secondary:

- primitive semantic segmentation
- symbol counting
- component retrieval

## Model size

Start at Brep2Shape scale:

- hidden dimension: 128
- heads: 4
- layers: 2/4/6
- target parameter count: 1.3M-3.3M before scaling

## Week-6 critical experiment

Label-efficiency curve:

- Train from scratch vs pre-train then fine-tune.
- Evaluate at 1%, 5%, 10%, 25%, 50%, 100% labeled drawings if feasible.
- Stop and diagnose if low-label relative gain is below 5%.

## Main risks

- FloorPlanCAD SVG annotations may not preserve enough DWG-native structure such as original block references.
- Text stream may be weak in FloorPlanCAD if text annotations are missing or not semantically bound.
- Baseline reproduction may be dominated by environment issues rather than modeling.
- Vector-to-raster reconstruction may be too easy unless masked/localized carefully.

