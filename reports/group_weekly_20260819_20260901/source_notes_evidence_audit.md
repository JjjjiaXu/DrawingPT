# 2026-08-19 至 2026-09-01 组会周报 source notes / evidence audit

生成日期：2026-09-01

## 1. 周报范围

- 时间范围：2026-08-19 至 2026-09-01，面向 2026-09-02 组会汇报。
- 受众：导师和组内同学。
- 上一期参考：`reports/group_meeting_2026-08-18/report.html`。
- 本期排除：服务器账号、密码、SSH key、服务器地址、个人绝对路径；未完成或无法核验的远端同步状态；用户私有草稿文件。

## 2. 已审计的信息来源

### 2.1 本地 Git 与工作区

- `git log --since=2026-08-19` 显示本期新增提交覆盖工程造价调研、DrawingPT v0 设计/资产冻结、训练 smoke、语义分类和 weighted loss 诊断。
- 本地最新提交：`8a91962 Document weighted semantic smoke results`。
- 服务器隔离工作副本已同步到 `8a91962`。
- GitHub 远端在本期生成时暂时停在 `e382efb`，因为本机多次连接 `github.com:443` 失败；因此本周报不声称最后两次提交已经推送到 GitHub。
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
- 不收录为正式结果：任何大规模训练、论文级 PQ/SQ/RQ、真实造价预测。

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
- 不收录：真实工程造价模型、真实单价或定额结果、BIM/CAD 私有项目数据。

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
- 不收录为新增完成：job 969 full-data baseline 本身，因为它已经属于上一期基础结果，不作为本期主要新增数字重复包装。

## 3. 未收录或降级处理的内容

1. 未收录服务器登录信息、密码、SSH key、服务器地址和用户个人绝对路径。
2. 未把 `1408` 写成完成实验；它只作为 PyTorch checkpoint 加载兼容性失败的诊断记录。
3. 未声称 CADTransformer 已经复现论文 PQ/SQ/RQ；当前证据只支持 primitive-level Total FG F1 与 PQ gate 未过。
4. 未声称 DrawingPT 预训练已经有效；当前 1% smoke 中 pretrained 只略高或不优于 scratch，不能作为有效性结论。
5. 未声称工程造价端到端模型已经实现；当前只有文献调研和 pseudo-BoQ 中间层。
6. 未把最后两次本地提交说成已经推到 GitHub；本地与服务器已同步，GitHub 远端最终 push 需要网络恢复后再做。

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
- `unchanged`：没有新证据或不应重复的项目状态。
- `timeline`：本期新增工作的时间线。
