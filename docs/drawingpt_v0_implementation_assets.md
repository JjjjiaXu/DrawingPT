# DrawingPT v0 实施资产冻结记录

生成日期：2026-09-01
范围：FloorPlanCAD 公开 11,602 张 SVG baseline split。

## 一句话结论

本轮已经把 DrawingPT v0 从“设计草案”推进到“可以开始写训练代码”的状态：primitive token manifest、低标注比例文件清单、每图 pseudo-BoQ 工程量 proxy 都已经生成，并记录了 hash。

## 1. Primitive token 数据管线

脚本：

```text
scripts/build_primitive_tokens.py
```

生成的可提交摘要：

| 资产 | SHA256 |
|---|---|
| `reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv` | `b6dd60a4976a3e5791eb8fc786a9cfbb24f1a9a466a5bb97d9aafd40b7412370` |
| `reports/next_steps_2026-09-01/floorplancad_token_summary.json` | `358b22e4e86797caf4d9927920a33e4dfce921824b838b262906c6b1f142bd65` |

本地样例 token JSONL 写在 `outputs/tokens/floorplancad_v0/tokens/`，不进入 Git。

### token 定义

v0 里每个 SVG geometry primitive 是一个 token。当前包含：

- primitive 类型：`path` / `circle` / `ellipse` / 预留 `line`、`polyline`、`polygon`、`rect`
- semanticId / instanceId
- bbox、归一化 bbox、中心点、宽高
- 近似长度 proxy、bbox 面积 proxy
- stroke width、fill/stroke 是否存在、style hash

### 全量统计

| split | SVG 文件数 | token 数 | semantic token 数 | 2048-token window 数 |
|---|---:|---:|---:|---:|
| train | 6,965 | 7,764,513 | 3,735,611 | 8,568 |
| val | 810 | 904,517 | 487,965 | 1,001 |
| test | 3,827 | 3,952,258 | 1,605,418 | 4,548 |
| all | 11,602 | 12,621,288 | 5,828,994 | 14,117 |

全数据 token 类型：

| 类型 | 数量 |
|---|---:|
| path | 12,454,181 |
| circle | 157,009 |
| ellipse | 10,098 |

文件级 token 数：min 6、median 544、mean 1,087.85、p90 2,298、max 53,919。也就是说大部分图 1-2 个 2048-token window 就能覆盖，但最大图会被切到 27 个 window。

### 重要限制

当前 bbox/length 是无外部依赖的稳定近似，尤其 path arc/Bezier 的几何包围盒不是精确 CAD 几何。它足够做 v0 的 token 特征和预训练 smoke，不应被当作真实物理量。

## 2. 低标注比例清单

脚本：

```text
scripts/build_label_fractions.py
```

生成位置：

- `configs/label_fractions/*.txt`
- `configs/label_fractions/manifest.csv`
- `configs/label_fractions/summary.json`

`manifest.csv` SHA256：

```text
7c9e55fdf58d06d9eaf6eb8af51e92e15d9d417920083231ba1e152ec273f603
```

| 比例 | 每个 seed 的 train 文件数 |
|---:|---:|
| 1% | 70 |
| 5% | 349 |
| 10% | 697 |
| 25% | 1,742 |
| 50% | 3,483 |
| 100% | 6,965 |

seed 固定为 304、1004、2026。同一个 seed 下，小比例清单是大比例清单的前缀；这能让 label-efficiency curve 更可比。

## 3. 每图 pseudo-BoQ 工程量 proxy 表

脚本：

```text
scripts/floorplancad_quantity_proxy.py
```

新增可提交资产：

| 资产 | 行数 | SHA256 |
|---|---:|---|
| `reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv` | 11,602 | `0060106a229f87606d49f6b4e220ed3eee86bc9ec0f2e406cda945f52e014679` |

每张图一行，主要字段包括：

- 门、窗、opening symbol 数量；
- 墙体、幕墙、栏杆长度 proxy；
- 楼梯、电梯、扶梯数量；
- 厨卫设备、厨房设备、空调、柜体数量；
- 车位 semantic element 数和长度 proxy；
- core semantic element / core instance / core length 总量。

训练集的几个汇总值：

| proxy | train 汇总 |
|---|---:|
| 门 instance | 34,704 |
| 窗 instance | 15,376 |
| 墙体长度 proxy | 8,836,841.492 |
| 楼梯 instance | 4,345 |
| 电梯 instance | 3,206 |
| 车位 semantic primitive | 148,711 |
| 厨卫设备 instance | 16,722 |
| 柜体 instance | 7,278 |

这张表解决的是“能不能把语义识别结果转成工程量中间层”。它不是造价表，因为缺少真实比例尺、墙高/厚度、材料做法、地区定额、单价和楼层信息。

## 4. 最小训练闭环 smoke 已补齐

本轮后续已经新增：

- `scripts/drawingpt_v0_dataset.py`
- `scripts/train_masked_primitive.py`
- `scripts/train_semantic_primitive.py`
- `scripts/server/drawingpt_v0_masked_smoke.sbatch`
- `scripts/server/drawingpt_v0_pretrain_short.sbatch`
- `scripts/server/drawingpt_v0_semantic_scratch_smoke.sbatch`
- `scripts/server/drawingpt_v0_semantic_pretrained_smoke.sbatch`
- `scripts/server/drawingpt_v0_semantic_weighted_smoke.sbatch`

本地 CPU smoke 结果见 `docs/drawingpt_v0_training_smoke.md`。

核心结论：

| 项目 | 结果 |
|---|---|
| Dataset smoke | 8/8 inspected windows feature 全为有限值 |
| feature dim | 13 |
| masked pretrain smoke | 5 step 正常前向/反向/更新 |
| loss | 1.786738 → 1.189145 |
| checkpoint | `outputs/checkpoints/drawingpt_v0_masked_smoke.pt`，不提交 Git |

注意：这是训练链路 smoke，不是正式模型结果。

服务器 100-step GPU smoke 也已完成：

| 项目 | 结果 |
|---|---|
| Slurm job | 1404 |
| device | CUDA / NVIDIA GeForce RTX 5090 |
| torch | 2.11.0+cu128 |
| steps | 100 |
| runtime | 57.583 秒 |
| loss | 2.643315 → 0.103848 |
| checkpoint SHA256 | `10adabe1b4f23f160d1488360bd406e9cd35d8074f1f9fe24ad7a50008077a62` |

进一步的 2048-token 和语义分类短跑也已完成：

| 实验 | job | 关键结果 |
|---|---:|---|
| 2048-token masked pretrain | 1405 | loss 1.642630 → 0.107217，checkpoint SHA256 `ceb52ad65ae94c69a9b0409fb2404b875f33a2de6975d5190862efb09d50317e` |
| semantic scratch，class 0 参与 loss | 1406 | all accuracy 0.521718，但 foreground accuracy/F1 为 0；诊断为 background shortcut |
| semantic scratch，foreground-only loss | 1407 | foreground accuracy 0.339074，macro F1 0.016764；不再全猜 background，但偏 wall/sink |
| semantic pretrained，foreground-only loss | 1409 | foreground accuracy 0.341238，macro F1 0.017662；加载 30 个 encoder key，略高于 scratch 但还不能宣称有效 |
| semantic weighted scratch，foreground-only loss | 1411 | foreground accuracy 0.251176，macro F1 0.020923；预测更分散但仍未解决长尾 |
| semantic weighted pretrained，foreground-only loss | 1412 | foreground accuracy 0.293149，macro F1 0.014104；没有优于 weighted scratch |

## 5. 下一步代码门禁

下一步不建议直接开大训练，应该先过下面门禁：

1. 类别均衡门禁：给 semantic fine-tuning 加 class-aware window sampling / focal loss，避免 wall/window/sink 高频类塌缩。
2. 1% 对照门禁：同一 seed0304 下重新跑 scratch vs pretrained，要求 foreground macro F1 明显高于当前 best smoke 0.0209。
3. 低标注曲线门禁：1%、5%、10% 至少各跑一个 seed，记录 runtime/checkpoint/hash。
4. pseudo-BoQ 预测门禁：把 semantic prediction 转成同字段 BoQ proxy，并和 GT 表算 count MAE / length error。

## 6. 组会可讲口径

> 我这周把 DrawingPT v0 的三个实验前资产冻结了。第一，FloorPlanCAD 全量 primitive token manifest 已生成，全数据 1262 万个 token，按 2048 token/window 是 14117 个 window；第二，1%、5%、10%、25%、50%、100% 的 train 文件清单已经按 3 个 seed 固定，并记录 hash；第三，我补了每张图一行的 pseudo-BoQ 表，可以把门窗数量、墙体长度 proxy、楼梯/电梯/车位/厨卫设备这些可计量中间层拿出来。下一步不急着宣称端到端造价，而是先验证“图纸表示学习 → 语义预测 → 工程量 proxy”的链路。

如果要加一句最新进展：

> 另外，DrawingPT v0 的最小训练闭环也已经跑通：Dataset 能输出 primitive window，masked primitive modeling 和 semantic classification 都能保存 checkpoint；服务器 2048-token pretrain 与 1% scratch/pretrained/weighted semantic smoke 已完成。当前发现的问题是短跑语义分类会向 wall/window/sink 高频类塌缩；class weighting 只带来很小改善，所以下一步先做 class-aware window sampling，再扩低标注曲线。
