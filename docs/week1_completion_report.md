# 第一周完成度报告

生成日期：2026-08-22
对照文档：`20260812_DrawingPT_Kickoff_Student_Shareable.md` 和 `docs/week1_plan.md`

## 总结

第一周主线任务已经完成，并且在 CADTransformer 基线复现上超过了原本“只需跑通 sample/smoke”的要求。

需要保留的 caveat 是：当前 job 969 是保守配置 baseline，不是论文严格复现。它证明环境、数据、训练和验证链路都通了，但还不能直接和 CADTransformer 论文数字对齐。

## 第一周清单对照

| 要求 | 状态 | 证据 |
|---|---|---|
| 建独立学术仓库 | 已完成 | 本地 git repo 已同步到 `JjjjiaXu/DrawingPT`，并遵守“不上传数据/权重/私有图纸”的纪律 |
| 只使用公开数据 | 已完成 | 当前只使用 FloorPlanCAD 公开版本 |
| 下载 FloorPlanCAD | 已完成 | 当前使用 11,602 张公开基线版本：train 6,965 / val 810 / test 3,827 |
| 跑通数据加载和扫描 | 已完成 | `scripts/scan_floorplancad.py`、`scripts/floorplancad_stats.py` 可用；本地 `outputs/reports/` 有统计产物 |
| 理解 SVG 标注字段 | 已完成 | `docs/floorplancad_data_report.md` 记录了 `semanticId`、`instanceId`、几何字段和 style 字段 |
| 确认 35 类任务链路 | 已完成 | CADTransformer 预处理、训练和验证已经读通 FloorPlanCAD 任务 |
| 调研 DWG/DXF 解析工具链 | 基本完成 | `scripts/inspect_dxf.py` 支持 DXF 图元、文字、图层、块引用解析；还缺公开 DXF 样例实测 |
| 调研开源基线 | 已完成 | `third_party/MANIFEST.md` 记录 CADTransformer、SymPoint、GAT-CADNet |
| 选择并跑通一个可执行基线 | 已完成 | CADTransformer smoke job 968 已完成 |
| 记录指标、runtime、硬件 | 已完成 | CADTransformer job 969：单卡 RTX 5090，10:21:28，best Total FG F1 = 0.827501 |
| 必读论文 10 行笔记 | 已完成 | FloorPlanCAD、CADSpotting、Brep2Shape、GeoPT、HouseMind、Text-Enhanced CAD、ArchPlanVQA |
| DrawingPT v0 设计草案 | 已完成 | `docs/drawingpt_v0_design_draft.md` |
| label-efficiency 协议草案 | 初步完成 | 已在 v0 草案里写出标注比例方向；正式 prereg 仍需补 |

## 新冻结资产

| 资产 | SHA-256 |
|---|---|
| HRNet-W48 ImageNet checkpoint | `0efec102d97f2ef58f0e258b2c3076b3704b93ffc2b73f64c8da5462c0037ef8` |
| CADTransformer smoke train log | `99a5f8a2bac787ec59336fc0562c27176b6e3f758e31de7126a0aa82f126ce57` |
| CADTransformer smoke best checkpoint | `86c534ef8d1bdec0efb37fecda5b3304dcd82ebf8a9ccdc16a5d062cae233302` |
| CADTransformer job 969 train log | `fe88160d0a83a5f0aa9b517d39901ce186f2682d9577e9376a05753267c917a4` |
| CADTransformer job 969 best checkpoint | `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530` |
| CADTransformer job 969 last checkpoint | `d29a4da0e541f1faf827fcdd41a612ba7ef1c0fa6ddbb69a1d7d9196db9df5db` |

## 新增数字

| run | 指标 | 数值 |
|---|---|---:|
| CADTransformer smoke，job 968 | Total FG Precision | 0.437268 |
| CADTransformer smoke，job 968 | Total FG Recall | 0.181527 |
| CADTransformer smoke，job 968 | Total FG F1 | 0.256508 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG Precision | 0.832457 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG Recall | 0.822702 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG F1 | 0.827501 |
| CADTransformer 保守 full-data baseline，job 969 | Runtime | 10:21:28 |

## 不该过度解读的地方

- job 969 使用 `img_size=384`，不是 CADTransformer 论文默认 700。
- job 969 使用 `rgb_dim=0`，没有走 `npy_rgb` 特征。
- 当前只有单次训练，没有多 seed。
- 当前还没有做跨 split 重复样本检查。
- 因此 job 969 是 baseline anchor，不是 paper-faithful reproduction。

## 第二周门禁

1. 决定是否恢复 `img_size=700`、`rgb_dim=32` 和 `npy_rgb`。
2. 做 train/val/test 跨 split 去重和同源图检查。
3. 用公开 DXF 样例验证 `inspect_dxf.py`，冻结 JSON 摘要 hash。
4. 将 DrawingPT v0 的 label-efficiency 曲线写成正式 prereg。
