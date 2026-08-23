# HouseMind - 10 行笔记

来源：arXiv:2603.11640，《Tokenization Allows Multimodal Large Language Models to Understand, Generate and Edit Architectural Floor Plans》。

1. HouseMind 代表平面图理解中的 VLM / MLLM 路线。
2. 它尝试把平面图理解、生成和编辑统一到一个多模态语言模型框架里。
3. 关键技术是离散 room-instance token，用 token 连接布局几何和符号推理。
4. 它和 DrawingPT 的重叠点是“把平面图 token 化”；不同点是 DrawingPT 从矢量 CAD 图元出发，目标是少标注表征学习。
5. HouseMind 更偏房间/布局层面的理解和生成，不是 FloorPlanCAD 这种图元级 panoptic symbol spotting。
6. 公平比较时不能简单让 VLM 输出所有 primitive instance，必须冻结 prompt、分辨率、裁剪和答案格式。
7. 对 DrawingPT 最有价值的 stress test 是精确计数、测量、符号定位和空间关系，而不是泛泛 caption。
8. 后续 VLM 对照实验要记录是否允许思维链、是否给坐标系、是否给图例/类别表。
9. 指标要按任务拆分：VQA 用 exact match / 数值误差，spotting 用 F1，生成用几何有效性和约束满足率。
10. 不能过度声称“VLM 不行”；更稳的主张是矢量原生路线在精确性、可审计性和样本效率上更适合工程图。
