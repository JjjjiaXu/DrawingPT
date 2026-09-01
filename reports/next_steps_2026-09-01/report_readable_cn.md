# DrawingPT 下一阶段推进记录

生成日期：2026-09-01

## 1. 本轮实际完成了什么

这轮不是直接开大训练，而是把开训前最容易“以后说不清”的三类资产先冻结下来：

1. **primitive token 数据管线**：把 FloorPlanCAD SVG 转成 DrawingPT v0 可用的 primitive token manifest。
2. **低标注比例清单**：固定 1%、5%、10%、25%、50%、100% 的 train 文件列表，并记录 seed/hash。
3. **每图 pseudo-BoQ 表**：把每张图的门窗数量、墙体长度 proxy、楼梯/电梯/车位/厨卫设备等工程量中间层做成表。

这三件事的价值是：后面不管模型结果好不好，都能追溯“用了哪些数据、哪些样本、怎样把图纸预测转成工程量 proxy”。

## 2. 新冻结资产和 hash

| 资产 | 说明 | SHA256 |
|---|---|---|
| `floorplancad_token_manifest_by_file.csv` | 每图 token/window 摘要，11,602 行 | `b6dd60a4976a3e5791eb8fc786a9cfbb24f1a9a466a5bb97d9aafd40b7412370` |
| `floorplancad_token_summary.json` | token 全局摘要 | `358b22e4e86797caf4d9927920a33e4dfce921824b838b262906c6b1f142bd65` |
| `configs/label_fractions/manifest.csv` | 18 组低标注清单索引 | `7c9e55fdf58d06d9eaf6eb8af51e92e15d9d417920083231ba1e152ec273f603` |
| `floorplancad_pseudo_boq_by_file.csv` | 每图 pseudo-BoQ 工程量 proxy，11,602 行 | `0060106a229f87606d49f6b4e220ed3eee86bc9ec0f2e406cda945f52e014679` |

这些都是从公开 FloorPlanCAD 派生的 compact 统计/清单；原始 SVG、processed NPY、checkpoint、全量 token JSONL 仍然留在本地或服务器，不提交 Git。

## 3. primitive token 数据：DrawingPT v0 可以开始接 Dataset 了

本轮新增脚本：

```text
scripts/build_primitive_tokens.py
```

v0 里，一个 SVG geometry primitive 对应一个 token。当前 token 包含：primitive 类型、semanticId、instanceId、bbox、归一化 bbox、中心点、宽高、近似长度 proxy、bbox 面积 proxy、stroke/fill 弱样式特征和 style hash。

全量统计：

| split | SVG 文件数 | token 数 | semantic token 数 | 2048-token window 数 |
|---|---:|---:|---:|---:|
| train | 6,965 | 7,764,513 | 3,735,611 | 8,568 |
| val | 810 | 904,517 | 487,965 | 1,001 |
| test | 3,827 | 3,952,258 | 1,605,418 | 4,548 |
| all | 11,602 | 12,621,288 | 5,828,994 | 14,117 |

全数据 token 类型：

| 类型 | 数量 | 占比 |
|---|---:|---:|
| path | 12,454,181 | 98.68% |
| circle | 157,009 | 1.24% |
| ellipse | 10,098 | 0.08% |

文件级 token 数：min 6、median 544、mean 1,087.85、p90 2,298、max 53,919。意思是大部分图 1-2 个 window 就能覆盖，但少数超大图需要切成多达 27 个 window。

重要限制：这里的 bbox/length 是为了机器学习输入做的稳定 proxy，不是精确 CAD 几何，也不是米或平方米。

## 4. 低标注比例：label-efficiency curve 的样本已经冻结

本轮新增脚本：

```text
scripts/build_label_fractions.py
```

输出位置：

```text
configs/label_fractions/
```

设置：

| 比例 | 每个 seed 的 train 文件数 |
|---:|---:|
| 1% | 70 |
| 5% | 349 |
| 10% | 697 |
| 25% | 1,742 |
| 50% | 3,483 |
| 100% | 6,965 |

seed 是 304、1004、2026。同一个 seed 下，小比例清单是大比例清单的前缀。这样后续画 label-efficiency curve 时，1%/5%/10% 的差异主要来自标注量变化，而不是样本完全换了一批。

注意：当前清单没有强行做类别均衡。rare class 如果表现波动，需要先看对应低标注子集有没有覆盖到足够样本。

## 5. 每图 pseudo-BoQ：补齐了“工程量中间层”表

本轮增强脚本：

```text
scripts/floorplancad_quantity_proxy.py
```

新增表：

```text
reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv
```

每张图一行，核心字段包括：

- 门、窗、opening symbol 数量；
- 墙体、幕墙、栏杆长度 proxy；
- 楼梯、电梯、扶梯数量；
- 厨卫设备、厨房设备、空调、柜体数量；
- 车位 semantic primitive 数和长度 proxy；
- core semantic element / core instance / core length 总量。

训练集几个关键汇总：

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

这一步不是在做真实造价，而是在做更可靠的中间任务：把图纸理解结果转成可解释的工程量 proxy。等 CADTransformer 或 DrawingPT 有预测 SVG/primitive prediction 后，就可以用同一口径生成预测侧 pseudo-BoQ，并计算误差。

## 6. CADTransformer PQ/SQ/RQ 门禁仍然单独保留

CADTransformer 当前 full-data conservative baseline 已经跑通，job 969 的 best validation Total FG F1 是 `0.827501`。但这仍不能当作论文 Table 1 的 PQ。

已确认的问题：

- 官方 README 提到 `scripts/evaluate_pq.py`；
- 当前 release 没有这个文件；
- 当前 `train_cad_ddp.py --val_only/--test_only` 只输出 primitive-level F1；
- 服务器检查没有发现 `npy_pred` 或 `svg_pred` prediction 目录；
- 当前训练入口没有完整接出 panoptic instance prediction。

所以组会建议口径是：

> CADTransformer 训练链路已跑通，但 PQ/SQ/RQ 评估门禁未过；当前只有 primitive-level Total FG F1，不能和论文 PQ/SQ/RQ 直接比较。

## 7. 最新推进：DrawingPT v0 最小训练闭环已经跑通

在数据资产冻结后，又补了两个核心代码文件：

```text
scripts/drawingpt_v0_dataset.py
scripts/train_masked_primitive.py
```

Dataset smoke：

| 项目 | 结果 |
|---|---:|
| inspected windows | 8 |
| feature dim | 13 |
| finite feature windows | 8 / 8 |
| valid tokens/window mean | 430.12 |

Masked primitive modeling smoke：

| step | loss | type loss | feature loss |
|---:|---:|---:|---:|
| 1 | 1.786738 | 1.462767 | 0.323970 |
| 2 | 1.642764 | 1.303607 | 0.339157 |
| 3 | 1.520735 | 1.192848 | 0.327887 |
| 4 | 1.362035 | 1.056409 | 0.305626 |
| 5 | 1.189145 | 0.895564 | 0.293581 |

这只是 CPU 上 5 step 的 smoke，不代表模型有效；但它证明了 Dataset、mask、Transformer forward/backward、loss、optimizer、checkpoint 保存这条链路已经通了。

服务器低资源 smoke 脚本也已跑通：

```text
scripts/server/drawingpt_v0_masked_smoke.sbatch
```

结果：

| 项目 | 结果 |
|---|---|
| Slurm job | 1404 |
| GPU | NVIDIA GeForce RTX 5090 |
| torch | 2.11.0+cu128 |
| window size | 512 |
| batch size | 8 |
| steps | 100 |
| runtime | 57.583 秒 |
| loss | 2.643315 → 0.103848 |
| checkpoint SHA256 | `10adabe1b4f23f160d1488360bd406e9cd35d8074f1f9fe24ad7a50008077a62` |

默认申请 1 张 GPU、30 分钟；本次实际约 58 秒完成，没有长期占卡。

## 8. 下周真正要过的门禁

| 门禁 | 通过标准 |
|---|---|
| 2048 window 门禁 | 使用 prereg 的 2048-token window 跑通 train 1% short epoch |
| fine-tuning 门禁 | 增加 semantic head，先跑 1% seed0304 scratch baseline |
| 低标注门禁 | 1%、5%、10% 至少各跑一个 seed，记录 runtime/checkpoint/hash |
| pseudo-BoQ 预测门禁 | 模型 prediction 能转成同字段 BoQ proxy，并和 GT 表算 count MAE / length error |
| CADTransformer PQ 门禁 | 找回官方 evaluation/export，或明确采用非官方 proxy PQ |
| 资源门禁 | 只在训练/评估时申请 GPU，不做无意义常驻占卡 |

## 9. 组会 1 分钟讲法

> 我这周没有直接跳到大训练，而是先把 DrawingPT v0 的实验资产冻结了。第一，FloorPlanCAD primitive token manifest 已生成，全数据 1262 万 token，按 2048 token/window 是 14117 个 window；第二，1%、5%、10%、25%、50%、100% 的 train 文件清单已经按 3 个 seed 固定，并记录 hash；第三，我补了每张图一行的 pseudo-BoQ 表，可以把门窗数量、墙体长度 proxy、楼梯/电梯/车位/厨卫设备这些中间工程量拿出来。最新进展是，Dataset 和 masked primitive modeling 的最小训练闭环已经跑通，服务器 100-step GPU smoke 也已经完成，约 58 秒跑完并保存 checkpoint。下一步进入 2048-token window short epoch 和 1%/5% 低标注 fine-tuning 对照；造价方向暂时不做黑箱总价，而是先验证“图纸表示学习 → 语义预测 → 工程量 proxy”的链路。
