# DrawingPT 第一周复现与调研报告（中文可读版）

生成日期：2026-08-23
项目阶段：第一周收口 / 第二周基线复现准备
结论口径：只讲公开数据、已冻结数字和下一步门禁；不提交原始数据、模型权重、私有图纸或服务器敏感信息。

## 1. 一句话结论

第一周的主线任务已经基本完成：FloorPlanCAD 数据已经下载、解析和统计；CADTransformer 已经在组内单卡 GPU 上跑通 smoke test 和一个 10 epoch 的保守 full-data baseline；第一批必读文献已经整理成 10 行笔记。

但要注意：目前的 CADTransformer 结果是“能跑通的保守基线锚点”，还不是论文严格复现。它使用了 `img_size=384` 和 `rgb_dim=0`，没有恢复 CADTransformer 原始设定里的 `img_size=700` 和 `rgb_dim=32/npy_rgb`。所以它可以用于证明环境和数据链路通了，但不能直接拿去和论文数字宣称对齐。

## 2. 组会只讲三件事

### 2.1 新冻结的资产

| 资产 | 数字 / hash | 说明 |
|---|---|---|
| FloorPlanCAD 处理后数据量 | train 6965 / val 810 / test 3827 | 三个 split 的 SVG/PNG/NPY 数量一致 |
| HRNet-W48 预训练权重 | `0efec102d97f2ef58f0e258b2c3076b3704b93ffc2b73f64c8da5462c0037ef8` | 本地加载，不提交权重文件 |
| CADTransformer smoke 日志 | `99a5f8a2bac787ec59336fc0562c27176b6e3f758e31de7126a0aa82f126ce57` | job 968 |
| CADTransformer smoke best checkpoint | `86c534ef8d1bdec0efb37fecda5b3304dcd82ebf8a9ccdc16a5d062cae233302` | 大文件不提交 |
| CADTransformer 正式训练日志 | `fe88160d0a83a5f0aa9b517d39901ce186f2682d9577e9376a05753267c917a4` | job 969 |
| CADTransformer 正式 best checkpoint | `642da46678d5f8d76cdeb958df4e6c77d5d9e3462a640467d9d83c6283a35530` | 大文件不提交 |

### 2.2 新增的数字

| 项目 | 指标 | 数值 |
|---|---|---:|
| CADTransformer smoke，job 968 | Total FG Precision | 0.437268 |
| CADTransformer smoke，job 968 | Total FG Recall | 0.181527 |
| CADTransformer smoke，job 968 | Total FG F1 | 0.256508 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG Precision | 0.832457 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG Recall | 0.822702 |
| CADTransformer 保守 full-data baseline，job 969 | Best Total FG F1 | 0.827501 |
| CADTransformer 保守 full-data baseline，job 969 | Runtime | 10:21:28 |

### 2.3 下周要过的门禁

1. 决定是否恢复 CADTransformer 论文默认设定：`img_size=700`、`rgb_dim=32`、补齐 `npy_rgb`。
2. 在恢复或明确放弃默认设定之前，不把 job 969 的 F1 当作论文复现数字。
3. 做 train / val / test 跨 split 重复样本检查，确认没有同源图或重复图泄漏。
4. 找一个公开 DXF 样例跑 `inspect_dxf.py`，冻结 JSON 摘要 hash，验证 DWG→DXF→矢量图元解析链路。

## 3. 第一周任务完成度

| MD 要求 | 当前状态 | 证据 |
|---|---|---|
| 建独立学术仓库 | 已完成 | GitHub 仓库已同步，且没有上传数据集/权重/私有信息 |
| 下载 FloorPlanCAD | 已完成 | 11,602 张公开版本：6965 / 810 / 3827 |
| 跑通数据加载和统计 | 已完成 | `docs/floorplancad_data_report.md` 和本地 `outputs/reports/*` |
| 确认 SVG 标注字段 | 已完成 | `semanticId`、`instanceId`、几何字段、style 字段已记录 |
| 调研 DWG/DXF 工具链 | 基本完成 | `scripts/inspect_dxf.py` 已支持 DXF 图元/文字/图层/块引用解析；还缺公开 DXF 样例实测 |
| 调研可复现基线 | 已完成 | CADTransformer / SymPoint / GAT-CADNet 已登记 |
| 至少跑通一个基线命令 | 已完成 | CADTransformer smoke job 968 |
| 记录指标、runtime、硬件 | 已完成 | job 969：RTX 5090，10:21:28，best F1 0.827501 |
| 必读论文 10 行笔记 | 已完成 | FloorPlanCAD、CADSpotting、Brep2Shape、GeoPT、HouseMind、Text-Enhanced CAD、ArchPlanVQA |
| DrawingPT v0 草案 | 已完成 | `docs/drawingpt_v0_design_draft.md` |

## 4. 真正跑过的复现：CADTransformer

### 4.1 为什么先复现 CADTransformer

CADTransformer 是目前最适合第一周打通链路的基线：它有公开代码、FloorPlanCAD 预处理脚本、HRNet 输入分支和训练入口。相比 SymPoint / GAT-CADNet，它更适合作为“先把数据和 GPU 环境跑通”的第一块石头。

### 4.2 跑通过程

整个过程不是一次成功，而是逐步排掉环境和兼容性问题：

| job | 状态 | 问题 / 结果 | 处理 |
|---:|---|---|---|
| 892 | CANCELLED | 早期预处理被中断 | 后续重跑 |
| 893 | FAILED | 缺少 `lxml` | 补依赖 |
| 894 | CANCELLED | `cairosvg` CLI 权限问题 | 改成 Python API |
| 895 | TIMEOUT | NPY 预处理超过 4 小时 | 改成可续跑、延长低资源任务 |
| 929 | COMPLETED | 全量 NPY 预处理完成 | 作为 smoke/full run 的数据基础 |
| 930 | FAILED | timm 缺 `_init_vit_weights` | 加兼容 shim |
| 965 | FAILED | NumPy 移除了 `np.int` | 补 NumPy alias 兼容 |
| 966 | FAILED | timm `default_cfg` 参数不兼容 | 改自定义 ViT 构造函数 |
| 967 | CANCELLED | 缺少可选 `npy_rgb` | 暂用 `rgb_dim=0` 跑保守配置 |
| 968 | COMPLETED | smoke test 跑通 | 验证训练链路 |
| 969 | COMPLETED | 10 epoch full-data 保守训练完成 | 冻结为第一版 baseline anchor |

### 4.3 当前结果怎么理解

job 969 的 best validation Total FG F1 是 `0.827501`。这个数字说明 CADTransformer 的训练、验证、checkpoint 保存、指标打印都跑通了，而且 full-data 训练没有崩。

但这个数字不能直接说“复现论文成功”，原因是配置不是论文默认：

- 当前 `img_size=384`，不是 CADTransformer 默认的 700。
- 当前 `rgb_dim=0`，跳过了可选 RGB feature。
- 当前是单次训练，没有多 seed，也没有 paper-faithful 对齐检查。
- 还没有做 train/val/test 跨 split 重复样本检查。

所以组会上最稳的说法是：**CADTransformer 已经作为保守 baseline anchor 跑通，best F1 0.827501；下一步要恢复或论证 paper-faithful 配置后再和论文数字比较。**

## 5. 其他文章/基线现在处于什么状态

| 文章 / 方法 | 当前状态 | 这周产出 | 下一步 |
|---|---|---|---|
| FloorPlanCAD | 数据集与主评测已吃透 | 数据报告、split 统计、标注字段说明 | 做跨 split 去重和泄漏检查 |
| CADTransformer | 已实际跑通 | smoke + 10 epoch full-data 保守 baseline | 恢复 `img_size=700`、`rgb_dim=32/npy_rgb` 后做 paper-faithful 复现 |
| CADSpotting | 已读文献，未复现 | 10 行笔记；确认它是重要监督基线 | 继续找官方代码；若无代码，暂作为 paper baseline |
| SymPoint | 已登记为候选 | repo/依赖/风险记录 | 如果 CADTransformer 对齐后还有时间，再尝试 point-based baseline |
| GAT-CADNet | 已登记为候选 | repo/依赖/风险记录 | 可作为轻量 sanity baseline |
| Brep2Shape | 已读文献 | 提炼为 DrawingPT v0 的 token 化/双流/自监督配方来源 | 把思想迁移到 2D 图元和文字流 |
| GeoPT | 已读文献 | 提炼 label-efficiency 曲线设计 | 复刻它的“少标注 vs 从零训练”评估方式 |
| HouseMind | 已读文献 | 明确 VLM/MLLM 对照边界 | 后续做 VLM 对比时冻结 prompt、分辨率和评分 |
| Text-Enhanced CAD | 已读文献 | 明确文本流 novelty 风险 | 论文表述不能说“首次 CAD+文本”，要收窄到自监督/矢量原生 |
| ArchPlanVQA | 已读元数据和任务定位 | 明确 VLM floor-plan VQA 对照方向 | 后续做计数/测量/空间关系 prompt suite |

## 6. 红线与纪律检查

本次同步到 GitHub 的内容遵守以下边界：

- 只使用公开数据集 FloorPlanCAD。
- 不碰、不上传业务方真实图纸。
- 不提交 raw dataset、processed dataset、checkpoint、PDF、大压缩包。
- 不提交服务器密码、服务器地址、私有 SSH key 或用户目录路径。
- 报告里只保留 hash、指标、配置和结论边界。
- 对未完成的 paper-faithful 复现明确写 caveat，不把保守运行包装成论文复现。

## 7. 下周建议安排

优先级从高到低：

1. **CADTransformer paper-faithful 门禁**：补 `npy_rgb`，恢复或评估 `img_size=700`，重新跑一个更接近论文设定的 baseline。
2. **数据泄漏检查**：对 train/val/test 做文件 hash、结构摘要、图元统计相似性检查。
3. **DXF 公共样例验证**：找公开 DXF 或生成合成 DXF，跑 `inspect_dxf.py`，冻结 JSON 摘要。
4. **DrawingPT v0 预训练协议**：把 label fractions、主指标、从零训练 baseline、seed 数写成正式 prereg。
5. **VLM 对照准备**：参考 HouseMind / ArchPlanVQA，冻结 prompt 和评分方式，但不要急着跑大规模 API。

## 8. 当前可放心引用的句子

> 第一周已经完成 FloorPlanCAD 数据链路和 CADTransformer 保守 baseline 跑通。全量保守训练 job 969 在单卡 RTX 5090 上完成，耗时 10:21:28，best validation Total FG F1 为 0.827501。这个结果证明环境、数据和训练链路已通，但还不是 paper-faithful 复现；下一步门禁是恢复或论证 `img_size=700`、`rgb_dim=32/npy_rgb` 配置，并做跨 split 泄漏检查。
