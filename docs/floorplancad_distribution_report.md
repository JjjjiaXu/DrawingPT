# FloorPlanCAD 图元分布与 CADTransformer 指标差距检查

生成日期：2026-08-23

本报告补齐第一周 checklist 中两项容易被追问的内容：

1. FloorPlanCAD 的图元类型、每图图元数量分布、35 类语义标注数量分布。
2. CADTransformer 论文指标 vs 本次复现指标 vs runtime，以及“差距超过 2 个点要找原因”的当前结论。

## 1. 数据统计口径

- 数据版本：当前仓库本地使用的是 CADTransformer / SymPoint / GAT-CADNet 公开脚本对应的 FloorPlanCAD 11,602 张版本。
- 统计对象：`train/train/svg_gt`、`val/val/svg_gt`、`test/test/svg_gt` 下的 SVG。
- raw SVG 图元类型统计：只统计实际出现的 SVG primitive tag，包括 `path`、`circle`、`ellipse`。
- 语义类别统计：统计带 `semanticId` 的 SVG 元素；它不是所有 raw SVG 图元的总数。
- instance 统计：只统计 `instanceId >= 0` 的实例，`-1` 视为 stuff/background-like 标注。

## 2. 每个 split 的图元数量分布

全量共有 11,602 张图，raw SVG primitive 共 12,621,288 个。单图 primitive 数的中位数为 544，均值为 1087.85，p95 为 3,541，最大值为 53,919。

| split | SVG 文件数 | raw primitive 总数 | 单图中位数 | 单图均值 | 单图 p95 | 单图最大值 | instance 均值 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| train | 6,965 | 7,764,513 | 540 | 1114.79 | 3,784 | 32,416 | 14.93 |
| val | 810 | 904,517 | 571 | 1116.69 | 3,350 | 53,919 | 14.76 |
| test | 3,827 | 3,952,258 | 551 | 1032.73 | 3,356 | 27,993 | 14.28 |

## 3. SVG 图元类型分布

`path` 占绝对多数，说明 FloorPlanCAD 虽然是 SVG 矢量格式，但对模型而言主要还是大量路径片段，圆和椭圆只占很小比例。

| SVG tag | 数量 | 占 raw primitive 比例 |
| --- | --- | --- |
| path | 12,454,181 | 98.68% |
| circle | 157,009 | 1.24% |
| ellipse | 10,098 | 0.08% |

## 4. 每张图的 raw primitive 数量桶

这个分布解释了为什么 baseline 训练容易遇到显存/时间问题：大多数图在 500-1,999 个 primitive 之间，但存在超过 10,000 primitive 的长尾大图。

| 单图 raw primitive 数 | SVG 文件数 | 占比 |
| --- | --- | --- |
| 0-99 | 530 | 4.57% |
| 100-499 | 4,895 | 42.19% |
| 500-999 | 2,641 | 22.76% |
| 1,000-1,999 | 2,125 | 18.32% |
| 2,000-4,999 | 1,043 | 8.99% |
| 5,000-9,999 | 289 | 2.49% |
| 10,000+ | 79 | 0.68% |

## 5. 语义标注数量分布

全量带 `semanticId` 的元素共 5,828,994 个，35 类在全量 train+val+test 中全部出现。注意 val split 只覆盖 33/35 类，缺少极少见的 revolving door 和 rolling door；因此小验证集上的 rare-class 波动会很大。

### Top 15 类

| class id | 类别 | 带 semanticId 元素数 | 占语义标注比例 | 出现 split |
| --- | --- | --- | --- | --- |
| 33 | wall | 1,362,387 | 23.37% | test+train+val |
| 12 | bed | 568,827 | 9.76% | test+train+val |
| 31 | row chairs | 541,080 | 9.28% | test+train+val |
| 19 | sink | 353,667 | 6.07% | test+train+val |
| 27 | toilet | 277,052 | 4.75% | test+train+val |
| 32 | parking spot | 271,245 | 4.65% | test+train+val |
| 13 | chair | 253,205 | 4.34% | test+train+val |
| 28 | stairs | 222,429 | 3.82% | test+train+val |
| 7 | window | 197,789 | 3.39% | test+train+val |
| 16 | Wardrobe | 183,836 | 3.15% | test+train+val |
| 1 | single door | 179,588 | 3.08% | test+train+val |
| 2 | double door | 173,840 | 2.98% | test+train+val |
| 34 | curtain wall | 139,157 | 2.39% | test+train+val |
| 25 | squat toilet | 126,250 | 2.17% | test+train+val |
| 29 | elevator | 102,054 | 1.75% | test+train+val |

### 最少 10 类

| class id | 类别 | 带 semanticId 元素数 | 占语义标注比例 | 出现 split |
| --- | --- | --- | --- | --- |
| 9 | blind window | 36,091 | 0.6192% | test+train+val |
| 21 | airconditioner | 31,452 | 0.5396% | test+train+val |
| 20 | refrigerator | 30,298 | 0.5198% | test+train+val |
| 15 | TV cabinet | 27,687 | 0.4750% | test+train+val |
| 30 | escalator | 22,138 | 0.3798% | test+train+val |
| 10 | opening symbol | 9,897 | 0.1698% | test+train+val |
| 8 | bay window | 6,071 | 0.1042% | test+train+val |
| 4 | folding door | 3,309 | 0.0568% | test+train+val |
| 5 | revolving door | 1,036 | 0.0178% | test+train |
| 6 | rolling door | 98 | 0.0017% | test+train |

## 6. CADTransformer 论文指标 vs 本次复现指标 vs runtime

CADTransformer 原论文 Table 1 的主指标是 panoptic symbol spotting 的 PQ/SQ/RQ；本次 job 969 日志冻结的是 `eval.py` 输出的前景 primitive 语义 Total FG Precision/Recall/F1。这两组不是同一口径，不能直接相减。

论文数值来源：CVPR 2022 论文 *CADTransformer: Panoptic Symbol Spotting Transformer for CAD Drawings* 的 Table 1。评估链路来源：官方 GitHub README 中的 `scripts/evaluate_pq.py` 说明。

| 指标 | 论文 CADTransformer | 论文 CADTransformer+RL | 本次 job 969 | 本次 runtime | 当前可比性 |
| --- | --- | --- | --- | --- | --- |
| PQ | 0.6732 | 0.6894 | 未产出 | 10:21:28 | 不可直接比较 |
| SQ | 0.8754 | 0.8832 | 未产出 | 10:21:28 | 不可直接比较 |
| RQ | 0.7226 | 0.7333 | 未产出 | 10:21:28 | 不可直接比较 |
| Total FG Precision | 未报告 | 未报告 | 0.832457 | 10:21:28 | 只可作为本次日志指标 |
| Total FG Recall | 未报告 | 未报告 | 0.822702 | 10:21:28 | 只可作为本次日志指标 |
| Total FG F1 | 未报告 | 未报告 | 0.827501 | 10:21:28 | 不可冒充论文主指标 |

## 7. “差距超过 2 个点要找原因”的当前结论

当前还不能计算严格的论文差距，因为本次没有产出论文主表所需的 PQ/SQ/RQ。这里的主要问题不是“差了几个点”，而是“指标口径还没对齐”。这本身就应该被记录为未过门禁项。

如果后续恢复 paper-faithful 配置并跑出 PQ/SQ/RQ，只要任一主指标与论文 CADTransformer+RL 差距超过 0.02 absolute，就按下面顺序排查：

1. **指标口径**：是否真的跑了 `evaluate_pq.py` 对应的 panoptic quality，而不是训练日志里的 Total FG F1。
2. **训练配置**：论文是 40 epochs、4 张 RTX A6000、HRNet 和 ViT backbone 预训练并 joint fine-tune；本次 job 969 是 10 epochs、1 张 RTX 5090、`img_size=384`、`rgb_dim=0`。
3. **输入特征**：本次没有生成/使用 `npy_rgb`，因此跳过 RGB feature 分支。
4. **数据版本与预处理**：当前是 11,602 张公开脚本版本；后续必须确认与论文 first version / 官方版本是否完全一致。
5. **增强策略**：论文最优行使用 Random Layer augmentation，本次未对齐。
6. **环境兼容补丁**：本次为了 Python 3.11、NumPy 1.26、timm 0.6.13 做过兼容补丁，paper-faithful 复现前要确认补丁没有改变模型语义。

## 8. 结论

这两项 checklist 现在的完成状态应写成：

- FloorPlanCAD 图元类型/数量分布：**已补齐**，并有可复用 CSV 摘要。
- 论文指标 vs 复现指标 vs runtime：**已补齐比较表，但 paper-faithful 指标尚未产出**；当前差距原因首先是指标和实验协议未对齐，而不是模型性能结论。

## 9. 公开来源

- CADTransformer CVPR 2022 论文：https://openaccess.thecvf.com/content/CVPR2022/papers/Fan_CADTransformer_Panoptic_Symbol_Spotting_Transformer_for_CAD_Drawings_CVPR_2022_paper.pdf
- CADTransformer 官方实现：https://github.com/VITA-Group/CADTransformer
- FloorPlanCAD 官网：https://floorplancad.github.io/
