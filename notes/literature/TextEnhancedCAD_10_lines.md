# Text-Enhanced Panoptic Symbol Spotting in CAD Drawings - 10 行笔记

来源：arXiv:2510.11091，《Text-Enhanced Panoptic Symbol Spotting in CAD Drawings》。

1. 这篇文章是 DrawingPT 的直接 novelty 风险，因为它已经把文本标注引入 CAD panoptic symbol spotting。
2. 它指出纯几何方法会忽略 CAD 图纸里的文字标注，也缺少对图元关系的显式建模。
3. 它把几何图元和文本图元放到统一表示里联合建模。
4. 它使用预训练 CNN 提取视觉特征，再接 Transformer backbone，而不是纯矢量原生自监督预训练。
5. 它的 type-aware attention 用来建模不同类型图元之间的空间依赖。
6. 与 DrawingPT 的直接重叠是“几何 + 文本/标注流”和 panoptic symbol spotting 目标。
7. DrawingPT 需要守住的差异是：自监督预训练、label-efficiency 曲线、矢量原生 token 化和预训练后 fine-tune。
8. 后续实验应该加入去掉文本流、去掉 relation/type-aware attention 的消融。
9. 新颖性表述不能写“首次使用 CAD 文本”，而应收窄到“矢量原生自监督预训练 + 可选文本流”。
10. 投稿前要确认这篇文章的数据集、指标和代码状态；若没有代码，可作为 paper baseline 并说明不可复现限制。
