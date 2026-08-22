# CADSpotting - 10-line note

1. CADSpotting targets panoptic symbol spotting on large-scale architectural CAD drawings.
2. Its central representation is dense point sampling along CAD primitives.
3. It deliberately avoids relying on fixed primitive types or layer information.
4. It uses a unified 3D point cloud model for semantic, instance, and panoptic segmentation.
5. It adds Sliding Window Aggregation with weighted voting and NMS for large drawings.
6. Experiments compare on FloorPlanCAD and LS-CAD.
7. What DrawingPT borrows: dense primitive sampling and windowed inference as a scalability baseline.
8. What DrawingPT should contrast: CADSpotting is supervised point-based; DrawingPT aims at self-supervised vector pre-training.
9. Current blocker: I did not find an official public code repo, so reproduction may need paper-only reimplementation or waiting for release.
10. Immediate use: treat CADSpotting as a result/method reference; use SymPoint/CADTransformer/GAT-CADNet for executable baselines first.

