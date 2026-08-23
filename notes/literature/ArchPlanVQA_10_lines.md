# ArchPlanVQA - 10 行笔记

来源：DOI 10.1061/JCCEE5.CPENG-7571，《ArchPlanVQA: Benchmark and Comprehensive Evaluation of Vision-Language Models for Understanding Architectural Floor Plan CAD Drawings》。

1. ArchPlanVQA 是第一周需要关注的 VLM / MLLM 平面图问答基准。
2. 它的重要性在于提醒我们：不能只引用“VLM 不行”，而要自己设计公平的 VLM 对照实验。
3. 它的任务形态是 VQA，不是检测或分割；更适合测 VLM 的图纸理解、计数、测量和空间关系推理。
4. DrawingPT 后续可以借它设计 prompt suite：符号计数、构件识别、尺寸读取、空间关系、文字标注关联。
5. 做 VLM 对照时必须冻结渲染分辨率、裁剪策略、prompt 模板、答案格式和评分脚本。
6. 指标要按答案类型拆开：分类题用 exact match，计数/测量题用数值误差，开放题尽量少用人工主观判断。
7. ArchPlanVQA 不能替代 FloorPlanCAD 的 panoptic symbol spotting；它是 raster/VLM 路线的补充评测。
8. 论文表述不能写成“VLM 完全做不了图纸”，更稳的说法是“矢量原生模型在精确、可审计、少标注场景更有优势”。
9. 如果后续调用商业 VLM API，要记录模型版本、调用日期、prompt、图像预处理和成本，因为结果会随模型版本变化。
10. 下一步：等 CADTransformer 复现稳定后，再做一小套 ArchPlanVQA 风格的计数/测量/空间关系对照。
