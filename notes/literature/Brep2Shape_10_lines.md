# Brep2Shape - 10-line note

1. Problem: B-rep is precise but abstract; sampled shape representations are intuitive but lossy.
2. Core idea: align boundary representation to shape representation through self-supervised prediction.
3. Input representation: decompose NURBS faces/edges into fixed-degree Bezier primitives.
4. Target representation: uniformly sampled spatial points on faces and edges.
5. Free supervision: sampled points are analytically computed from the same B-rep, so no labels are needed.
6. Architecture: Dual Transformer with separate face and edge streams.
7. Topology prior: attention bias comes from shared edge/face tokens, not just binary adjacency.
8. Key result: scaling data and model depth improves both pre-training loss and downstream performance.
9. What DrawingPT borrows: tokenization, dual stream, topology-aware attention, free alignment target, label-efficiency evaluation.
10. What differs: DrawingPT is 2D DWG/DXF, needs a text/annotation stream, and uses vector-to-raster rendering as the free target.

