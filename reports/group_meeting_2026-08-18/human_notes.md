# 作者填写（B 层）

> ⚠️ 这五个字段必须由作者本人填写，AI 不许代笔。
> 每个字段至少 15 个有效字符；写完后再运行 `make_report.py --check`。

---

## 跑之前我预测这个数是多少

<!-- 请把 prereg.txt 第 2 条直接抄到这里。若本轮属于补写，请明确写“本轮没有有效跑前预测”。 -->
这一实验我没有明确的跑前预测。

## 哪个数出乎我意料, 为什么

<!-- 至少选一个数，例如 smoke F1、正式训练速度、训练 loss、验证 F1、数据过滤数量等；写为什么意外。 -->
smoke F1 = 0.256508：只跑 1 epoch、保守设定、禁用 ViT 在线预训练、rgb_dim=0，还能完整走通并给出非零 F1。

## 我改了什么才让它跑通

<!-- 请用你自己的话写调试史。可参考但不要照抄：timm 兼容、NumPy 旧别名、ViT 初始化、禁用在线 ViT 权重、rgb_dim=0、Slurm QoS 调整。 -->
处理了 timm 的 ViT 初始化和 `default_cfg` 参数兼容问题；当时 smoke test 已跑通，后续正式 job 969 也已完成，结果以 A 层冻结表格为准。

## 如果这个结论是错的, 最可能错在哪一步

<!-- 请指出你认为最脆弱的一步，例如 smoke 只验证链路不代表正式性能、rgb_dim=0 改变了原始设定、img_size=384 不是论文默认 700、缺少 npy_rgb。 -->
还需要确认 train/val/test 是否有跨 split 重复或数据泄漏，可能存在数据泄露？

## 哪几个数我敢在会上被追问, 哪几个不敢

<!--
请逐条列：
敢：____
不敢：____
-->
敢被追问：FloorPlanCAD 三个 split 数量、HRNet 权重 hash、smoke 指标、job 969 的 best F1/runtime/checkpoint hash。不敢直接拿去和论文数字比较：因为当前 job 969 是 img_size=384、rgb_dim=0 的保守配置，还不是 paper-faithful 复现。

---

## 本次与上次的差异

本次补充了 job 969 完成后的正式 baseline 数字与 hash。

## 已知未解决的问题

尚未恢复 paper-faithful 的 `img_size=700`、`rgb_dim=32/npy_rgb` 配置；还需要做跨 split 重复样本检查。
