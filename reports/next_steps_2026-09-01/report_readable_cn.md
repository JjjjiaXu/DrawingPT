# DrawingPT 下一阶段三件事推进记录

生成日期：2026-09-01

## 1. 本轮推进了什么

本轮把下一阶段最关键的三件事推进到了可汇报状态：

1. **CADTransformer PQ/SQ/RQ 门禁**：确认当前不是训练失败，而是公开 release 缺少完整 PQ 评估链路。
2. **DrawingPT v0 prereg**：把低标注自监督预训练实验写成正式协议草案。
3. **FloorPlanCAD 工程量 proxy**：从 11,602 张 SVG 真实统计出门窗、墙体、楼梯、车位、厨卫设备等 proxy 表。

## 2. CADTransformer PQ/SQ/RQ：当前是“门禁未过”，不是“结果为 0”

CADTransformer 当前保守 full-data baseline 已经完成，job 969 的 best validation Total FG F1 是 `0.827501`。但这仍然不能当成论文 Table 1 的 PQ。

原因：

- 官方 README 提到 `scripts/evaluate_pq.py`；
- 当前 release 的 `scripts/` 目录里没有这个文件；
- `train_cad_ddp.py --val_only/--test_only` 只输出 primitive-level F1；
- 服务器只读检查没有发现 `npy_pred` 或 `svg_pred` 预测目录；
- 当前模型入口只返回 semantic logits，没有完整接出 panoptic instance prediction。

因此下次组会最稳的说法是：

> CADTransformer 训练链路已经跑通，但 PQ/SQ/RQ 评估门禁未过。原因是 release 缺少 README 所述的 PQ 评估脚本和预测导出链路，目前只有 primitive-level Total FG F1，不能和论文 PQ/SQ/RQ 直接比较。

后续建议：并行推进 DrawingPT v0，同时继续追官方 PQ evaluation/export 代码；不要让缺失脚本卡住主线。

## 3. DrawingPT v0：正式 prereg 已经补齐

v0 的研究问题被收束为：

> 2D CAD/SVG/DXF 的矢量 primitive 自监督预训练，能否在 FloorPlanCAD 少标注 fine-tuning 场景下带来稳定收益？

冻结设置：

| 项目 | 设置 |
|---|---|
| 预训练数据 | FloorPlanCAD train split |
| 下游数据 | FloorPlanCAD train/val/test |
| token | `path` / `circle` / `ellipse` primitive |
| 主自监督目标 | masked primitive modeling |
| 标注比例 | 1%、5%、10%、25%、50%、100% |
| seed | 304、1004、2026 |
| 主要指标 | micro F1、macro F1、rare-class F1；PQ/SQ/RQ 取决于评估链路 |
| 成功门槛 | 低标注区间绝对提升 ≥ 0.02 或 relative improvement ≥ 5% |

这让 DrawingPT v0 不再只是“想法”，而是一个能真正执行和失败诊断的实验协议。

## 4. 工程量 proxy：已经从 FloorPlanCAD 统计出第一版表

本轮脚本从 FloorPlanCAD 公开 11,602 张 SVG 中统计了工程量相关 proxy。

全局数字：

| 指标 | 数值 |
|---|---:|
| SVG 文件数 | 11,602 |
| train / val / test | 6,965 / 810 / 3,827 |
| 每图核心语义元素中位数 | 186 |
| 每图核心非负实例数中位数 | 7 |
| 每图核心近似 SVG 长度中位数 | 1,812 |

训练集里最重要的工程量 proxy：

| 角色 | 语义元素数 | 非负实例数 | 覆盖文件比例 | 近似 SVG 长度 |
|---|---:|---:|---:|---:|
| 墙体/围护 | 991,664 | 0 | 96.50% | 9,814,343 |
| 开口/门窗 | 421,488 | 50,996 | 77.59% | 2,520,288 |
| 垂直交通 | 212,847 | 7,904 | 47.75% | 2,439,014 |
| 厨卫/设备点位 | 720,068 | 20,940 | 33.93% | 0 |
| 柜体/固定家具 | 187,546 | 7,278 | 12.42% | 0 |
| 车位 | 148,711 | 0 | 9.15% | 992,790 |

解释：

- 门窗适合做 instance count；
- 墙体/幕墙/栏杆适合做长度 proxy；
- 厨卫设备适合做点位清单 proxy；
- 车位适合做平面布置/数量 proxy，但 `instanceId` 不可靠；
- 这些还不是米、平方米或元，只是面向工程量的图纸中间层。

## 5. 下次组会建议讲法

可以这样讲：

> 我把后续路线拆成三件可验证的事。第一，CADTransformer 的训练链路已经通，但 PQ/SQ/RQ 评估门禁还没过，主要原因是 release 缺少 README 提到的评估脚本和预测导出链路。第二，DrawingPT v0 已经写成正式 prereg，主问题是 primitive 自监督预训练能否提升 FloorPlanCAD 低标注 fine-tuning。第三，为了回应工程造价方向，我没有直接做总价黑箱预测，而是先从 FloorPlanCAD 统计门窗、墙体、楼梯、车位和厨卫设备的工程量 proxy。下一步可以用 CADTransformer/DrawingPT 的预测结果生成同样的 proxy 表，比较工程量误差。

## 6. 下周真正要过的门禁

| 门禁 | 通过标准 |
|---|---|
| CADTransformer PQ 门禁 | 找回官方 evaluation/export，或明确采用非官方 proxy PQ |
| DrawingPT v0 数据门禁 | token dataset 能从 train split 生成固定窗口，输出文件列表 hash |
| 低标注采样门禁 | 1/5/10/25/50/100% train 文件列表固定，记录 seed 和 hash |
| 工程量 proxy 门禁 | 能从 GT 和模型预测两边生成同口径 proxy 表 |
| 资源门禁 | GPU 只用于必要训练/评估，不用时不占卡 |
