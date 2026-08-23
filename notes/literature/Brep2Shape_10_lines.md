# Brep2Shape - 10 行笔记

1. Brep2Shape 解决的是 3D B-rep CAD 表示精确但难学习、采样点表示直观但有损的问题。
2. 它的核心思想是用自监督方式对齐边界表示和形状表示。
3. 输入端把 NURBS 面/边分解成固定阶 Bézier 基元 token。
4. 目标端从同一个 B-rep 解析出面/边上的采样点，因此监督信号不需要人工标注。
5. 模型结构是双流 Transformer，分别处理 face stream 和 edge stream。
6. 拓扑先验来自面-边共享关系，而不是只靠普通空间距离。
7. 关键启发是：小模型 + 合适的几何 token + 免费自监督目标，也能带来下游收益。
8. DrawingPT 可以借鉴 token 化、双流结构、拓扑注意力和 label-efficiency 评估。
9. DrawingPT 与它不同：我们是 2D DWG/DXF/矢量图纸，需要额外处理文字、图层、块引用和工程标注。
10. 对 DrawingPT 最直接的迁移是“图元流 + 文字流”双流模型，以及“矢量图元 → 栅格局部渲染”的自监督目标。
