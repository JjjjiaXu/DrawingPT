# CADSpotting - 10 行笔记

1. CADSpotting 面向建筑 CAD 图纸上的 panoptic symbol spotting，是 DrawingPT 必须关注的强监督基线。
2. 它的核心表示是沿 CAD 图元进行密集点采样，把矢量图纸转成点云式输入。
3. 这种方法刻意减少对固定图元类型、图层命名等工程规范的依赖。
4. 模型目标同时覆盖 semantic、instance 和 panoptic 层面的符号识别。
5. 大图推理时使用 sliding window aggregation，并结合加权投票/NMS 合并局部结果。
6. 实验主要对比 FloorPlanCAD 和 LS-CAD 等 CAD 图纸数据集。
7. DrawingPT 可以借鉴它的大图窗口化推理和“沿图元采样”的 scalability 处理方式。
8. DrawingPT 需要与它形成清晰区别：CADSpotting 是监督点基线，DrawingPT 是自监督矢量预训练。
9. 当前风险是没有稳定确认官方公开代码，因此短期不能保证能直接复现。
10. 现阶段处理方式：把 CADSpotting 作为 paper baseline 和方法参考，先用 CADTransformer/SymPoint/GAT-CADNet 做可执行基线。
