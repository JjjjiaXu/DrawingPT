#### Evidence Log - 20260901

本轮围绕“DrawingPT 是否能作为 FloorPlanCAD 上的矢量原生自监督预训练前端”推进。核心不是追一个单点高分，而是先把研究问题、数据资产、训练入口和可比较实验口径搭起来。

本期可核验增量集中在四件事：文献定位、FloorPlanCAD 数据画像、DrawingPT v0 训练闭环、工程量 pseudo-BoQ 中间层。共整理 7 篇 CAD / 平面图 / 几何预训练 / VLM 相关文献笔记；处理 11,602 张 SVG；冻结 12,621,288 个 primitive token、14,117 个 2048-token window、18 组低标注 split；完成 1% seed0304 下 scratch/pretrained 1000-step controlled run。

本期排除口径：上一期已经完成的 baseline 复现结果，以及不可横向比较、只用于检查入口是否能跑通的 smoke 数字，不再作为本轮组会成果单列。

1.

##### Last Meeting's Actions

| **Action** | **Status** | **Evidence / Result** |
| :--- | :--- | :--- |
| 明确 DrawingPT v0 的研究定位 | Done | 文献调研后将近期问题收窄为“vector-native primitive token + self-supervised pretraining + low-label evaluation” |
| 整理 CAD / 平面图 / 几何预训练相关文献 | Done | 完成 FloorPlanCAD、CADSpotting、Brep2Shape、GeoPT、ArchPlanVQA、HouseMind、TextEnhancedCAD 共 7 篇 10-line notes |
| 冻结 FloorPlanCAD primitive token 资产 | Done | 11,602 张 SVG；12,621,288 个 primitive token；按 2048-token window 得到 14,117 个 windows |
| 冻结低标注训练清单 | Done | 生成 1%、5%、10%、25%、50%、100% 六档比例，seed 为 304、1004、2026，共 18 组 split |
| 补齐 FloorPlanCAD 数据画像 | Done | raw primitive 中 path 占 98.68%；semanticId 元素 5,828,994 个；wall 占 23.37%，rolling door 仅 98 个 |
| 跑通 DrawingPT v0 预训练入口 | Done | 2048-token masked primitive pretrain short 中 loss 从 1.642630 降到 0.107217，并冻结 checkpoint hash |
| 诊断 semantic 训练失效模式 | Done | 确认 background/unlabeled 参与 loss 会造成 all accuracy 虚高、foreground F1 失效；后续改为 foreground-only loss |
| 实现 class-aware sampler 与采样审计 | Done | 1% seed0304 下 class-aware 采样一轮 unique windows 为 46/88；rare token share 从 8.48% 到 8.82% |
| 完成 1% seed0304 正式 controlled run | Done | scratch 与 pretrained 两组 1000-step run 均完成；pretrained macro F1=0.0320，高于 scratch 的 0.0270；rare macro F1=0.0083，高于 scratch 的 0.0022 |
| 调研工程造价方向并构造 pseudo-BoQ 中间层 | Done | 生成 11,602 行 per-file pseudo-BoQ，包含门窗数量、墙体长度 proxy、楼梯/电梯/车位/厨卫设备等字段 |

2.

##### Blockers

| **Blocker** | **当前影响** | **后续需要确认** |
| :--- | :--- | :--- |
| DrawingPT v0 目前仍是 1% 单 seed 小模型结果 | 可以作为正式受控实验汇报，但不能作为论文级充分结论 | 是否优先扩展到 1%/5%/10% × scratch/pretrained × 多 seed |
| semantic macro F1 绝对值仍低 | pretrained 有正向信号，但模型仍被 wall、toilet、double door、window 等高频类主导 | 下一轮优先比较 focal loss、更强 class-aware sampler、longer schedule 还是更大模型 |
| FloorPlanCAD baseline 是 SVG/semantic proxy | 当前结果能支撑图纸语义理解与工程量 proxy，不能等同于完整 DWG/BIM 工程数据 | 是否能获得比例尺、材料做法、楼层、真实 BoQ、单价或造价标签 |
| pseudo-BoQ 仍是研究中间层 | 能验证 quantity takeoff 思路，但不能说成真实造价估算 | 是否先做预测侧 pseudo-BoQ 误差评估，还是先做合成单价 demo |

3.

##### Decisions / Learnings

1. **近期主线应是 DrawingPT 低标注预训练收益曲线。** 现在最值得回答的问题不是“v0 分数高不高”，而是“同样标注比例下，预训练是否稳定优于 scratch”。
2. **数据画像已经解释了为什么不能只看 overall accuracy。** FloorPlanCAD 的 path 和 wall 都非常高频，稀有类极端稀疏；后续必须同时报告 foreground macro F1、rare F1、per-class support 和 dominant predictions。
3. **background/unlabeled 需要被显式控制。** 早期训练已经暴露 shortcut：如果直接把 background 放进 loss，模型会得到看似不错的 all accuracy，但前景类别没有真正学到。
4. **class-aware sampler 是必要但不充分的改动。** 它改变了训练窗口暴露分布，但真正效果要以 full-val controlled run 为准。
5. **1000-step controlled run 给出了正向但有限的预训练信号。** pretrained 在 foreground accuracy、macro F1、rare macro F1 和 val loss 上均优于 scratch，但幅度仍小，需要多比例、多 seed 才能判断是否稳定。
6. **工程造价方向更适合作为应用落点，而不是直接作为当前模型目标。** 当前更稳的链路是“图纸理解 → 构件/符号/工程量 proxy → pseudo-BoQ → 真实 BoQ/造价”。

4.

##### Next Meeting's Actions

建议下一轮以 **DrawingPT 低标注预训练收益曲线** 作为主线，同时推进 **预测侧 pseudo-BoQ** 和 **小型 VLM prompt baseline** 两个辅助验证。

| **Priority** | **Action** | **Expected Output** |
| :--- | :--- | :--- |
| P0 | 确认近期主研究问题 | 明确是否以“矢量原生自监督预训练能否提升低标注 CAD primitive 理解”为核心问题 |
| P0 | 扩展 controlled run 到 1%/5%/10% × scratch/pretrained | 输出 label-efficiency curve，至少包含 foreground accuracy、macro F1、rare F1、per-class support 和 runtime |
| P1 | 做高频类塌缩消融 | 比较 class-aware sampler、focal loss、inverse-sqrt weighting、longer schedule 对 rare F1 的影响 |
| P1 | 生成预测侧 pseudo-BoQ | 与 GT pseudo-BoQ 计算 count MAE、count relative error 和 length proxy error |
| P2 | 设计小型 VLM prompt baseline | 固定渲染、prompt 和评分规则，测试计数、测量和空间关系类任务 |
