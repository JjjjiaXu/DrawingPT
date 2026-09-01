# 2026-08-19 至 2026-09-01 组会周报 source notes / evidence audit

生成日期：2026-09-01

## 1. 周报范围

- 时间范围：2026-08-19 至 2026-09-01，面向 2026-09-02 组会汇报。
- 受众：导师和组内同学。
- 上一期参考：`reports/group_meeting_2026-08-18/report.html`。
- 本期排除：服务器账号、密码、SSH key、服务器地址、个人绝对路径；无法核验的远端同步状态；用户私有草稿文件。

## 2. 已审计的信息来源

### 2.1 本地 Git 与工作区

- `git log --since=2026-08-19` 显示本期新增提交覆盖工程造价调研、DrawingPT v0 设计/资产冻结、训练 smoke、语义分类和 weighted loss 诊断。
- 本地最新提交：`8a91962 Document weighted semantic smoke results`。
- 服务器隔离工作副本已同步到 `8a91962`。
- GitHub 远端同步状态不进入组会正文；本周报以本地 evidence 文件和 SHA-256 为核验依据。
- 工作区唯一未跟踪文件是 `reports/group_meeting_2026-08-18/talk_script_cn.md`，它是既有讲稿草稿，本周报不收录为证据。

### 2.2 DrawingPT v0 数据与训练证据

可核验证据：

- `reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv`
  - SHA-256：`b6dd60a4976a3e5791eb8fc786a9cfbb24f1a9a466a5bb97d9aafd40b7412370`
  - 说明：11,602 张 SVG 的 token/window 文件级统计。
- `reports/next_steps_2026-09-01/floorplancad_token_summary.json`
  - SHA-256：`358b22e4e86797caf4d9927920a33e4dfce921824b838b262906c6b1f142bd65`
  - 说明：全局 token 数、split、primitive 类型分布。
- `reports/next_steps_2026-09-01/label_fraction_manifest.csv`
  - SHA-256：`7c9e55fdf58d06d9eaf6eb8af51e92e15d9d417920083231ba1e152ec273f603`
  - 说明：1%、5%、10%、25%、50%、100% 低标注清单索引，seed 为 304、1004、2026。
- `reports/next_steps_2026-09-01/drawingpt_v0_server_gpu_smoke_job1404_summary.json`
  - SHA-256：`015411eedcc5f5fbbbff845652d89d5483a0070a08c6fd4d1ca9234c8895ea18`
  - 说明：服务器 512-token masked pretrain GPU smoke。
- `reports/next_steps_2026-09-01/drawingpt_v0_server_gpu_semantic_smoke_20260901_summary.json`
  - SHA-256：`8152c6a01f7de324f7583d510ba15e1948b400a12c7b0ff2de01fdd456951663`
  - 说明：2048-token pretrain、semantic scratch/pretrained/weighted smoke 的 compact 摘要。
- `docs/drawingpt_v0_training_smoke.md`
  - SHA-256：`9579fe83e7b55777428216db1026e516fb33299ebc1b555fb4406945d2fc5244`
  - 说明：训练闭环解释、关键 job 和指标边界。

本周报收录判断：

- 收录：数据资产冻结、低标注清单、2048-token pretrain、semantic smoke、background shortcut 诊断、weighted loss 初步结果。
- 阶段边界：本期只把大规模训练、论文级 PQ/SQ/RQ、真实造价预测列为后续门禁，不作为已完成成果。

### 2.3 工程造价与 pseudo-BoQ 证据

可核验证据：

- `reports/engineering_cost_research_2026-08-23/report_readable_cn.md`
  - SHA-256：`3c08cc30d4819c6843c05e23ad0a254320a5cdd24d2378cb821bf20ff9c276ed`
  - 说明：工程造价自动估算调研汇报。
- `docs/floorplancad_quantity_proxy_report.md`
  - SHA-256：`8b4d11e7ba992c0505b82118107d78e0859ceff772722dc1e59ad304e23abe26`
  - 说明：FloorPlanCAD 工程量 proxy 统计口径。
- `reports/next_steps_2026-09-01/floorplancad_pseudo_boq_by_file.csv`
  - SHA-256：`0060106a229f87606d49f6b4e220ed3eee86bc9ec0f2e406cda945f52e014679`
  - 说明：每图 pseudo-BoQ 表，11,602 行。
- `reports/next_steps_2026-09-01/floorplancad_quantity_proxy_summary.json`
  - SHA-256：`4861553816d22a7d2a7f97c8206bdb09f958f7ea9f03bb845af40ad7d3471d6c`
  - 说明：pseudo-BoQ 汇总指标。

本周报收录判断：

- 收录：造价方向成熟度判断、DrawingPT 作为图纸理解前端的定位、pseudo-BoQ 中间层资产。
- 阶段边界：真实工程造价模型、真实单价或定额结果、BIM/CAD 私有项目数据属于后续资源需求。

### 2.4 CADTransformer 评估门禁证据

可核验证据：

- `docs/cadtransformer_pq_gate.md`
  - SHA-256：`d83faf136d84090faf1f97289e522088661dfb6834f63fb1cfbd2d730a6297be`
  - 说明：PQ/SQ/RQ 评估门禁审计。
- `reports/group_meeting_2026-08-18/report.html`
  - SHA-256：`47293168f3be3cc042a7459fae9b03dee50b8da1cbb57718e4ccfce8f173db8b`
  - 说明：上一期可读报告，用于避免重复旧结果。
- `reports/next_steps_2026-09-01/report_readable_cn.md`
  - SHA-256：`38c7539956d5a4fdeb7d24355d99d4fbe1f037fe28b6af34d6d89d20b4486581`
  - 说明：当前下一阶段综合报告。

本周报收录判断：

- 收录：CADTransformer 当前只能作为 primitive-level semantic baseline；PQ/SQ/RQ 未过门禁。
- 阶段边界：job 969 full-data baseline 属于上一期基础结果，本期只引用它作为 semantic baseline 锚点。

## 3. 阶段边界和降级处理

1. 服务器登录信息、密码、SSH key、服务器地址和用户个人绝对路径不进入周报。
2. `1408` 作为 PyTorch checkpoint 加载兼容性诊断记录，不作为完成实验。
3. CADTransformer 本期定位为 semantic baseline 与 PQ/SQ/RQ 评估链路审计；论文主指标走 official/proxy 门禁。
4. DrawingPT 预训练当前只支持 smoke 结论；有效性要等低标注曲线验证。
5. 工程造价方向当前是文献定位和 pseudo-BoQ 中间层；真实造价模型需要后续 BoQ、单价、材料和造价标签。
6. GitHub 远端同步状态不进入组会正文；需要网络恢复后再做最终 push。

## 4. 报告结构选择

采用技术受众报告结构：

1. 标题
2. 技术摘要
3. 带证据的关键发现
4. 范围、数据和指标定义
5. 方法/实验设计
6. 限制、不确定性和鲁棒性检查
7. 推荐下一步
8. 进一步问题

在 `work-summary-v1` 中，这些角色映射为：

- `meeting_summary`：组会一页。
- `projects[].headline/progress/metrics/comparison`：关键发现、证据和定义。
- `projects[].boundary`：可信边界、限制和不确定性。
- `projects[].next`：推荐下一步和门禁。
- `unchanged`：本次正文不渲染该块，避免把阶段边界呈现为失败清单。
- `timeline`：本期新增工作的时间线。
