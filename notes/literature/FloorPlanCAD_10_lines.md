# FloorPlanCAD - 10 行笔记

1. FloorPlanCAD 是 DrawingPT 当前最重要的公开 benchmark。
2. 它提供真实建筑 CAD 图纸的 SVG 矢量表示，并带有符号级标注。
3. 官网提到后续有 15,663 张图纸版本；当前复现链路使用公开基线脚本常用的 11,602 张版本。
4. 当前本地 split 为 train 6,965、val 810、test 3,827。
5. 任务是 panoptic symbol spotting：既要识别类别，也要区分可数对象实例。
6. SVG 中可以读到 `semanticId`、`instanceId`、路径/圆/椭圆等几何字段和样式字段。
7. 它适合作为 DrawingPT 的主评测数据，因为任务和“工程图符号理解”直接对齐。
8. 主要局限是 SVG 版本可能丢失 DWG 原生结构，例如块定义、块引用、完整图层语义。
9. 类别分布很不均衡，稀有类别在低标注比例实验中可能消失，需要单独关注。
10. 下一步是做跨 split 重复样本检查，并把指标口径从当前 Total FG F1 对齐到更严格的 panoptic/instance 评估。
