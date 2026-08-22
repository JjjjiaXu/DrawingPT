# GeoPT - 10-line note

Source: arXiv:2602.20399, "GeoPT: Scaling Physics Simulation via Lifted Geometric Pre-Training".

1. GeoPT is not a CAD-symbol-spotting baseline; it is a protocol reference for proving that pre-training reduces downstream label demand.
2. Its key idea is lifted geometric pre-training: static geometry is augmented with synthetic dynamics so pre-training is closer to the target physics task.
3. The transferable lesson for DrawingPT is to avoid an overly easy pretext task; vector-to-raster reconstruction should be masked/localized enough to teach usable structure.
4. Its headline evaluation style is label efficiency: compare downstream performance with less labeled data against a from-scratch model under the same budget.
5. DrawingPT should copy that evaluation shape with FloorPlanCAD label fractions such as 1%, 5%, 10%, 25%, 50%, and 100%.
6. The y-axis should be the one declared spotting metric, preferably Total FG F1 for early work and the proper panoptic/instance metric once evaluation is complete.
7. Essential ablations to copy: no pre-training, smaller/larger model, less/more pre-training data, frozen encoder versus full fine-tuning, and objective variants.
8. Scaling axes for DrawingPT: public drawing count, primitive-window count, model depth/width, text-stream on/off, and topology/layer attention on/off.
9. The closest DrawingPT analogue is pre-training on FloorPlanCAD plus public DXF/SVG drawings, then fine-tuning the same detector on labeled FloorPlanCAD fractions.
10. Do not cite GeoPT as direct evidence for 2D CAD; cite it as motivation for the label-efficiency experiment design and the 20-60% labeled-data-reduction narrative to test.
