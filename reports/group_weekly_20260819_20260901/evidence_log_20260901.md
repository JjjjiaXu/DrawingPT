#### Evidence Log - 20260901

本轮围绕“DrawingPT 能否作为 FloorPlanCAD 上的矢量原生自监督预训练前端”推进了文献调研、数据资产冻结、训练链路诊断和服务器正式受控实验。共整理 7 篇 CAD/平面图/VLM/几何预训练相关文献笔记，处理 FloorPlanCAD baseline 中 11,602 张 SVG，冻结 12,621,288 个 primitive token、14,117 个 2048-token window 和 18 组低标注清单。

调研与实验重点是判断 DrawingPT 的合理研究定位：不是再做一个普通强监督 CAD 检测器，而是用 vector-native primitive token 做自监督预训练，并在低标注比例下验证 scratch 与 pretrained 的差异。

1.

##### Last Meeting's Actions

| **Action** | **Status** | **Evidence / Result** |
| :--- | :--- | :--- |
| 建立并同步 DrawingPT 学术仓库 | Done | GitHub 仓库已同步本期代码、报告、脱敏实验结果和 evidence 文件 |
| 下载并处理 FloorPlanCAD baseline 数据 | Done | 处理 11,602 张 SVG，生成 12,621,288 个 primitive token 和 14,117 个 2048-token window |
| 统计 FloorPlanCAD 图元类型、数量分布和 35 类语义标注 | Done | path 占 98.68%；semanticId 元素共 5,828,994 个；wall 占 23.37%，rolling door 仅 98 个 |
| 调研 CAD / 平面图 / 几何预训练相关工作 | Done | 整理 FloorPlanCAD、CADSpotting、Brep2Shape、GeoPT、ArchPlanVQA、HouseMind、TextEnhancedCAD 共 7 篇文献笔记 |
| 完成 DrawingPT v0 token 化和低标注清单设计 | Done | 固定 1%、5%、10%、25%、50%、100% train 清单，seed 为 304、1004、2026 |
| 跑通 masked primitive pretrain 与 semantic primitive classification 链路 | Done | 服务器完成 2048-token masked pretrain short，loss 从 1.642630 降到 0.107217，并保存 checkpoint |
| 诊断 semantic smoke 的失效模式 | Done | 发现 background/unlabeled 参与 loss 会导致 foreground F1 为 0；改为 foreground-only loss 后继续比较 scratch/pretrained/weighted |
| 实现 class-aware sampler 和 exposure audit | Done | 1% seed0304 下 class-aware 采样一轮覆盖 46/88 个 unique windows，rare token share 从 8.48% 到 8.82% |
| 完成 1% seed0304 正式 controlled run | Done | scratch job 1440 与 pretrained job 1441 均 COMPLETED/ExitCode 0:0；pretrained macro F1=0.0320，高于 scratch 的 0.0270 |
| 调研工程造价方向并构造 pseudo-BoQ 中间层 | Done | 生成 11,602 行 pseudo-BoQ 表，包含门窗数量、墙体长度 proxy、楼梯/电梯/车位/厨卫设备等字段 |

2.

##### Blockers

| **Blocker** | **当前影响** | **后续需要确认** |
| :--- | :--- | :--- |
| 当前 DrawingPT v0 仍是 1% 单 seed 小模型结果 | 可以汇报为正式受控实验完成，但不能作为论文级充分结论 | 是否立刻扩展到 1%/5%/10% × scratch/pretrained × 多 seed |
| semantic macro F1 绝对值仍低 | pretrained 相比 scratch 有正向信号，但模型仍受 wall、toilet、double door、window 等高频类影响 | 是否优先尝试 focal loss、更强 class-aware sampler、longer schedule 或更大模型 |
| FloorPlanCAD baseline 是 SVG/semantic proxy，不是完整 DWG/BIM 工程数据 | 当前结果能支持图纸语义理解和工程量 proxy，不能直接支持真实工程造价 | 是否能获得真实 BoQ、单价、材料、比例尺或 BIM/CAD 工程项目数据 |
| pseudo-BoQ 目前是研究中间层 | 可用于验证 quantity takeoff 思路，但不能说成真实造价估算结果 | 下一步是否做预测侧 pseudo-BoQ，并用 count MAE、relative error、length proxy error 评估 |

3.

##### Decisions / Learnings

1. **DrawingPT 的核心定位应收窄为 vector-native primitive token + self-supervised pretraining。** 这样能避开“又一个强监督 CAD 检测器”的风险，也能与现有监督 spotting 方法形成清楚分工。
2. **低标注曲线比单个高分更适合作为近期主线。** 当前已经冻结 1%、5%、10%、25%、50%、100% 清单，下一步应围绕 scratch vs pretrained 的 label-efficiency curve 展开。
3. **background/unlabeled 不能直接参与 semantic loss。** 早期 smoke 已证明这会造成表面 accuracy 虚高、foreground F1 为 0 的 shortcut，因此后续语义实验必须坚持 foreground-only 或显式控制 background。
4. **class-aware sampler 是必要的，但不是充分条件。** 它能改变窗口暴露分布；真正效果仍要看 full-val macro F1、rare F1、per-class support 和 dominant predictions。
5. **正式 1000-step controlled run 给出了正向但有限的预训练信号。** pretrained 在 foreground accuracy、macro F1、rare macro F1 和 val loss 上均优于 scratch，但幅度还小，必须通过多比例、多 seed 才能形成可信结论。
6. **工程造价方向不应直接承诺端到端总价。** 更稳的研究链路是“图纸理解 → 构件/符号/工程量 proxy → pseudo-BoQ → 真实 BoQ/造价”，当前成果适合定位为工程量中间层。

4)

##### Next Meeting's Actions

建议下一轮以 **DrawingPT 低标注预训练收益曲线** 作为主线，同时保留 **pseudo-BoQ 应用验证** 和 **小型 VLM prompt baseline** 两条支线。

| **Priority** | **Action** | **Expected Output** |
| :--- | :--- | :--- |
| P0 | 确认 DrawingPT v0 的主研究问题 | 明确是否以“矢量原生自监督预训练是否提升低标注 CAD primitive 理解”为近期核心问题 |
| P0 | 扩展 1%/5%/10% × scratch/pretrained × 多 seed controlled run | 输出 label-efficiency curve，至少包含 foreground accuracy、macro F1、rare F1、per-class support 和 runtime |
| P1 | 针对高频类塌缩做损失函数和采样消融 | 比较 class-aware sampler、focal loss、inverse-sqrt weighting、longer schedule 对 rare F1 的影响 |
| P1 | 把 semantic prediction 转成预测侧 pseudo-BoQ | 用 GT pseudo-BoQ 计算 count MAE、count relative error 和 length proxy error |
| P2 | 设计一个小型 VLM prompt baseline | 固定渲染、prompt 和评分规则，测试计数、测量、空间关系等图纸理解任务 |
