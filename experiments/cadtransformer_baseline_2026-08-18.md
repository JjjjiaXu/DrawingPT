# CADTransformer 保守基线复现实验记录

## 日期

提交时间：2026-08-18
完成时间：2026-08-19

## 代码状态

提交作业时的本地代码状态：`5b545dc`（`Use normal QoS for conservative CADTransformer training`）。

## 数据集版本

FloorPlanCAD 公开 11,602 张版本：

- train：6,965；CADTransformer 训练过滤后保留 6,962
- val：810
- test：3,827

说明：这是 CADTransformer / SymPoint / GAT-CADNet 公开脚本常用的 Google Drive 版本，不是官网后续提到的 15,663 张更新版。

## 硬件

YaoGroup Slurm 服务器，单卡 NVIDIA GeForce RTX 5090。

## 运行入口

通过 `scripts/server/cadtransformer_train.sbatch` 提交。

关键配置：

- epochs：10
- image size：384
- batch size：1
- test batch size：1
- workers：0
- `rgb_dim=0`
- 禁用 ViT 在线下载预训练权重
- HRNet-W48 ImageNet 预训练权重从本地文件加载

## 运行时间

Slurm job 969：

- state：`COMPLETED`
- exit code：`0:0`
- start：2026-08-18 19:27:38 CST
- end：2026-08-19 05:49:06 CST
- elapsed：10:21:28

## 指标

训练过程中验证集打印的 Total FG 指标：

| epoch 标记 | Total FG Precision | Total FG Recall | Total FG F1 |
|---|---:|---:|---:|
| Epoch 1 | 0.750009 | 0.713377 | 0.731184 |
| Epoch 2 | 0.793087 | 0.768256 | 0.780424 |
| Epoch 6 / Best Epoch 5 | 0.832457 | 0.822702 | 0.827501 |

当前 best model 按验证集 Total FG F1 选择：

`0.827501118183136`

## 冻结产物

| 产物 | 大小 | SHA-256 |
|---|---:|---|
| train log | 64,635 bytes | `fe88160d0a83a5f0aa9b517d39901ce186f2682d9577e9376a05753267c917a4` |
| best model | 1,085,562,061 bytes | `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530` |
| last model | 1,085,562,061 bytes | `d29a4da0e541f1faf827fcdd41a612ba7ef1c0fa6ddbb69a1d7d9196db9df5db` |
| Slurm stdout | - | `61fe8aab418f82659b9b6dc4c2c18bdcb1b33b8d1946b5ffdf1d6e57d9f65d9f` |
| Slurm stderr | - | `200b84a634f5c01233da19b23986357b863ed74803bf017225dbe62f95675ac8` |

大模型文件不提交到 git，只记录 hash。

## 与论文数字的关系

当前还不能计算严格的“与论文数字差多少”，因为这次运行不是 paper-faithful 配置，而且本次日志指标和论文主指标不是同一口径。

CADTransformer 原论文 Table 1 的主指标是 panoptic symbol spotting 的 PQ/SQ/RQ：

| 指标 | 论文 CADTransformer | 论文 CADTransformer+RL | 本次 job 969 |
|---|---:|---:|---:|
| PQ | 0.6732 | 0.6894 | 未产出 |
| SQ | 0.8754 | 0.8832 | 未产出 |
| RQ | 0.7226 | 0.7333 | 未产出 |
| Total FG Precision | 论文未报告 | 论文未报告 | 0.832457 |
| Total FG Recall | 论文未报告 | 论文未报告 | 0.822702 |
| Total FG F1 | 论文未报告 | 论文未报告 | 0.827501 |

本次 `Total FG F1` 来自 CADTransformer `eval.py`，是前景 primitive 语义分类累计指标；论文 Table 1 的 PQ/SQ/RQ 是 panoptic symbol spotting 指标。因此它们不能直接相减，也不能把 `0.827501` 写成论文复现 PQ。

主要差异：

- 论文训练 40 epochs；本次只训练 10 epochs。
- 论文使用 4 张 NVIDIA RTX A6000；本次使用 1 张 NVIDIA GeForce RTX 5090。
- 使用 `img_size=384`，不是原始默认 700。
- 使用 `rgb_dim=0`，没有使用 `npy_rgb` 特征。
- 本次未使用 Random Layer augmentation。
- 本次尚未跑 README 中的 panoptic quality 评估链路。
- batch size、workers 等也为了稳定和节省资源做了保守设置。

因此这次结果的定位是：**证明 CADTransformer 在当前服务器、当前 FloorPlanCAD 版本、当前兼容补丁下已经完整跑通；它是 baseline anchor，不是最终论文复现数字。**

后续如果跑出 PQ/SQ/RQ，任一主指标与论文 CADTransformer+RL 差距超过 0.02 absolute，再按指标口径、训练配置、输入特征、数据版本、增强策略和兼容补丁逐项排查。

## 调试记录

前置失败主要来自环境和兼容问题：

- 缺少 `lxml`；
- CairoSVG CLI 权限问题；
- NumPy 旧别名被移除；
- timm ViT API 变化；
- optional `npy_rgb` 文件缺失；
- Slurm QoS / 资源设置需要调整。

最终 job 969 有 Python multiprocessing / NCCL 清理 warning，但 Slurm exit code 是 `0:0`，best/last checkpoint 都已保存，所以不视为训练失败。
