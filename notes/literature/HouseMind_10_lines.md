# HouseMind - 10-line note

Source: arXiv:2603.11640, "Tokenization Allows Multimodal Large Language Models to Understand, Generate and Edit Architectural Floor Plans".

1. HouseMind represents the VLM/MLLM route for floor plans: unify understanding, generation, and editing through tokenization and instruction tuning.
2. Its input is architectural floor-plan structure, but its center of gravity is room/layout reasoning rather than CAD primitive-level symbol spotting.
3. The important technical idea is discrete room-instance tokens that bridge layout geometry and symbolic reasoning.
4. This overlaps with DrawingPT at the broad "tokenize floor plans" level, but differs because DrawingPT starts from vector CAD primitives and targets low-label representation learning.
5. A fair comparison should not ask HouseMind to output every primitive instance unless the prompt, resolution, and answer format are carefully controlled.
6. For DrawingPT, HouseMind is most useful as a VLM-style baseline for room/layout understanding and controllable editing, not as a direct CADTransformer replacement.
7. Counting and measurement should be treated as stress tests: ask exact symbol counts, dimensions, and object localization rather than vague captioning.
8. Prompt protocol must be frozen before evaluation, including image rendering resolution, crop policy, coordinate convention, and whether chain-of-thought is hidden.
9. Comparable metrics should be task-specific: exact-match / numeric error for VQA, detection/F1 for spotting, and validity/constraint satisfaction for generation.
10. Do not overclaim that VLMs "cannot do floor plans"; the safer claim is that vector-native structure should be more sample-efficient and more auditable for precise engineering tasks.
