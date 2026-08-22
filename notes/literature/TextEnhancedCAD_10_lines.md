# Text-Enhanced Panoptic Symbol Spotting in CAD Drawings - 10-line note

Source: arXiv:2510.11091, "Text-Enhanced Panoptic Symbol Spotting in CAD Drawings".

1. This is a direct novelty-risk paper for DrawingPT because it explicitly adds textual annotations to CAD panoptic symbol spotting.
2. The paper argues that geometry-only methods miss rich textual annotations and under-model relationships among CAD primitives.
3. Its representation jointly models geometric primitives and textual primitives, so DrawingPT cannot claim "first to use text in CAD spotting".
4. It initializes from pretrained CNN visual features and then uses a Transformer-style backbone, rather than being purely vector-native self-supervised pre-training.
5. A type-aware attention mechanism models different spatial dependency types among primitives and text.
6. The direct overlap is the geometry-plus-text/annotation stream and the panoptic symbol spotting target.
7. The key difference to protect is DrawingPT's self-supervised pre-training objective, label-efficiency evaluation, and vector-native tokenization before supervised fine-tuning.
8. For experiments, this paper suggests an ablation that removes text primitives and another that removes relation/type-aware attention.
9. For novelty wording, say "self-supervised vector-native pre-training with optional text stream", not "first text-enhanced CAD understanding model".
10. Before submission, compare against this paper's reported dataset, metric, and public code status; if no code exists, use it as a paper baseline and cite the limitation.
