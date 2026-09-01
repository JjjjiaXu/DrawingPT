# DrawingPT v0 1000-step 正式受控实验结果

生成日期：2026-09-01

## 实验设置

本次实验固定为 1% seed0304、2048-token window、class-aware sampler、inverse-sqrt class weighting。两组作业串行运行：scratch 先跑，pretrained 通过 Slurm `afterok` 依赖在 scratch 成功后启动。两组均申请 1 张 GPU，实际训练设备为 `cuda`。

## 主结果

| job | 设置 | steps | val windows | runtime | foreground acc | macro F1 | rare macro F1 | Slurm 状态 |
|---:|---|---:|---:|---:|---:|---:|---:|---|
| 1440 | scratch | 1000 | 1001 | 123.6s | 0.2048 | 0.0270 | 0.0022 | COMPLETED / 0:0 |
| 1441 | pretrained | 1000 | 1001 | 124.7s | 0.2178 | 0.0320 | 0.0083 | COMPLETED / 0:0 |

pretrained 相比 scratch 的变化：

- foreground accuracy：+0.0130
- foreground macro F1：+0.0050
- rare macro F1：+0.0062
- validation loss：-0.2176

## 解释边界

这组实验已经不是入口 smoke，而是固定设置下的正式受控对照；但它仍然只是 1% 单 seed 的 v0 小模型结果。pretrained 的收益是正向但幅度不大，不能写成论文级充分结论。

模型仍受高频类别主导。scratch 的 top predictions 主要集中在 wall、double door、sink、toilet、single door；pretrained 的 top predictions 主要集中在 wall、toilet、double door、window、stairs。下一步必须扩到 5%、10% 和多 seed，并持续汇报 per-class support、dominant predictions 与 rare F1。

## 脱敏说明

本文件保留 Slurm job 状态、实验设置、指标和 checkpoint SHA-256；服务器绝对路径、账号连接信息和密码不进入该证据文件。
