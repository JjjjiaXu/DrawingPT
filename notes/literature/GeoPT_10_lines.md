# GeoPT - 10 行笔记

来源：arXiv:2602.20399，《GeoPT: Scaling Physics Simulation via Lifted Geometric Pre-Training》。

1. GeoPT 不是 CAD 符号检测基线，而是“如何证明预训练减少标注需求”的实验设计参考。
2. 它的核心思想是 lifted geometric pre-training：给静态几何加入合成动态，让预训练更接近目标物理任务。
3. 对 DrawingPT 的启发是：预训练任务不能太简单，否则 vector-to-raster 重建可能学不到有用结构。
4. 它的关键叙事是 label efficiency：同样下游任务下，比较少标注 fine-tuning 和从零训练。
5. DrawingPT 可以照搬这种评估形态：例如 1%、5%、10%、25%、50%、100% 标注比例。
6. 早期 y 轴可以用 Total FG F1；正式论文阶段应切到更严格的 panoptic/instance 指标。
7. 必做消融包括：无预训练、不同模型大小、不同预训练数据量、冻结/全量 fine-tune、不同自监督目标。
8. DrawingPT 的 scaling 轴可以是公开图纸数量、图元窗口数量、模型层数/宽度、文字流开关、拓扑/图层注意力开关。
9. 最近似的 DrawingPT 实验是：先用公开 SVG/DXF 图纸预训练，再在 FloorPlanCAD 不同比例标注上 fine-tune。
10. 不能把 GeoPT 当成 2D CAD 已经有效的证据；只能把它作为标注效率曲线和预训练叙事的参考。
