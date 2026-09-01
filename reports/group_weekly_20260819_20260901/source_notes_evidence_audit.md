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
- 本期核心代码与证据提交以 `8a91962 Document weighted semantic smoke results` 为界；后续提交主要是周报组织与表达调整。
- 服务器隔离工作副本同步状态不进入组会正文；本周报以本地 evidence 文件和 SHA-256 为核验依据。
- GitHub 远端同步状态只在交付说明中报告，不作为组会正文证据。
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
- `scripts/train_semantic_primitive.py`
  - SHA-256：`994c665a0e8fc25c09483458f50fd3fbaa145665518a964a215d0b44d6a1f2fd`
  - 说明：语义分类、foreground-only loss、class weighting 与 class-aware sampler 实现。
- `scripts/train_masked_primitive.py`
  - SHA-256：`b9004146270e240deaea0a136e3995e535db555d617448c0b2fb91831725772f`
  - 说明：masked primitive pretrain 与 Transformer nested tensor 兼容补丁。
- `scripts/audit_class_aware_sampler.py`
  - SHA-256：`f8fe59cfbb66983c8e6e30169150f5ea2a012c8d835ff5c87913ec448d4cce7b`
  - 说明：class-aware sampler 暴露审计脚本。
- `reports/next_steps_2026-09-01/drawingpt_v0_classaware_sampler_audit.json`
  - SHA-256：`5723c50453666aaf90d735ac28a91f119eb7322849d7ef84dfbe59a25485787f`
  - 说明：1% seed0304 class-aware sampler exposure audit。
- `reports/next_steps_2026-09-01/drawingpt_v0_classaware_sampler_audit.md`
  - SHA-256：`efb95848fe939cc006c01d2c56f1ca075905b7fa489cdb2dae015cf0fdbe2988`
  - 说明：class-aware sampler exposure audit 可读版。
- `reports/next_steps_2026-09-01/drawingpt_v0_semantic_classaware_weighted_cpu20_summary.json`
  - SHA-256：`7dbbb877a4a4f9cda72ddc831c9420e47a0da5978e20f3efd392212f1866dbb9`
  - 说明：本机 CPU 20-step class-aware+weighted sanity summary。
- `scripts/server/drawingpt_v0_semantic_scratch_smoke.sbatch`
  - SHA-256：`d12c66842e23e10f548ab61c47c80c664d0114569af827bba94992c56e84bfb9`
  - 说明：scratch semantic smoke 服务器脚本，支持 `SAMPLER` 透传。
- `scripts/server/drawingpt_v0_semantic_pretrained_smoke.sbatch`
  - SHA-256：`51b9c04204d268825bebf0925b480b7b9d97c1abaf17cca503b7b0c4a2c54527`
  - 说明：pretrained semantic smoke 服务器脚本，支持 `SAMPLER` 透传。
- `scripts/server/drawingpt_v0_semantic_weighted_smoke.sbatch`
  - SHA-256：`c00dbee06adf5a5111606f64a9a9031ee2af6cb249269fd5e579c0ef97ba8d1c`
  - 说明：weighted semantic smoke 服务器脚本，支持 `SAMPLER` 透传。
- `docs/drawingpt_v0_formal_experiment_plan.md`
  - SHA-256：`5f35323f3b723eff2766d867e3e5d6f3158aaaf0e090ac10aea68167376cd26a`
  - 说明：DrawingPT v0 1000-step controlled run 计划，固定 1% seed0304、class-aware sampler、scratch vs pretrained、full val。
- `scripts/server/drawingpt_v0_semantic_controlled.sbatch`
  - SHA-256：`4bea342b654199d7c95b3363216894423a050fa0640c0128a123cbf6d55032b7`
  - 说明：正式 semantic controlled run 单作业 Slurm 脚本。
- `scripts/server/submit_drawingpt_v0_classaware_controlled_pair.sh`
  - SHA-256：`491264018da829415ffc6cfffe5079533224d432eace3651de5bbcb5e99afb31`
  - 说明：scratch→pretrained 串行 controlled pair 提交脚本。
- `scripts/summarize_semantic_controlled_results.py`
  - SHA-256：`877b5211fab2a15d8e76c53c75e7143d3d3d8ccc31e89fe7ee9cf938cbaf0eeb`
  - 说明：controlled run 结果汇总脚本。

本周报收录判断：

- 收录：数据资产冻结、低标注清单、2048-token pretrain、semantic smoke、background shortcut 诊断、weighted loss 初步结果、class-aware sampler 实现、sampler exposure audit、本机 CPU sanity 和 1000-step controlled run 计划/脚本。
- 阶段边界：sampler exposure audit 不是模型效果；本机 CPU 20-step sanity 不与服务器 100-step smoke 横向比较；1000-step controlled run 当前作为正式实验入口和门禁计划收录，只有实际 Slurm summary 产出后才能写成实验完成；本期只把大规模训练、论文级 PQ/SQ/RQ、真实造价预测列为后续门禁，不作为已完成成果。

### 2.3 FloorPlanCAD 数据画像与长尾风险证据

可核验证据：

- `docs/floorplancad_distribution_report.md`
  - SHA-256：`6d00254388e664c2804330e1158920392672ad1fdd936ad92f5dee2652258ee0`
  - 说明：FloorPlanCAD 图元类型、每图图元数量桶、35 类语义标注分布和 CADTransformer 指标口径检查。
- `docs/floorplancad_data_report.md`
  - SHA-256：`3b8903e1c7f46112f92afda393a020f58bc4e09b388e4945066b5e6e7bda02c8`
  - 说明：FloorPlanCAD 数据版本、文件结构、SVG 标注字段和核心统计说明。
- `reports/group_meeting_2026-08-18/floorplancad_tag_distribution.csv`
  - SHA-256：`bc839f21f8f22d3da42dc31bcdcca8b2d84444a04b32c9ac8db5fb7974a27f63`
  - 说明：path、circle、ellipse 的 raw SVG primitive tag 分布。
- `reports/group_meeting_2026-08-18/floorplancad_primitive_count_bins.csv`
  - SHA-256：`ad0bb0f7e7e097358a86c1c407e7e06073930c30c8709d384d6310904c08265d`
  - 说明：每张图 raw primitive 数量分桶。
- `reports/group_meeting_2026-08-18/floorplancad_semantic_distribution.csv`
  - SHA-256：`d7f38ec0fa3bde8a81e4c9a0ba1fb179402b04b3845b758d6cb05dbac65452eb`
  - 说明：FloorPlanCAD 35 类 semanticId 元素分布。

本周报收录判断：

- 收录：raw primitive 类型分布、单图规模长尾、semantic 类别长尾、val 稀有类缺失，以及这些统计如何支撑 class-aware sampling 和 rare-class F1 门禁。
- 阶段边界：这些统计解释数据与评估风险，不作为模型性能提升证据。

### 2.4 CAD/平面图文献调研与方法定位证据

可核验证据：

- `notes/literature/FloorPlanCAD_10_lines.md`
  - SHA-256：`e42bdc31d4027a0b16627319b703f2b7011c1330b23f41508edcd3c1edf4419e`
  - 说明：FloorPlanCAD benchmark、SVG 标注结构、split 和数据边界。
- `notes/literature/CADSpotting_10_lines.md`
  - SHA-256：`3e5d3a95483b5ac27fbef0b098ac91628e725ec912393afb87146acf1b86ea14`
  - 说明：监督 CAD panoptic symbol spotting baseline 参考。
- `notes/literature/Brep2Shape_10_lines.md`
  - SHA-256：`21c843af54989b10af78b908ae6f2fb212930814191416c54cc8dcd93e2e03e1`
  - 说明：几何自监督预训练、token/拓扑建模和 label-efficiency 参考。
- `notes/literature/GeoPT_10_lines.md`
  - SHA-256：`ed2aa281ebdc5b2cc3bcb68f3bea3dbd1309d65170965f87f9e10c59d1bf772f`
  - 说明：预训练规模、低标注比例和消融设计参考。
- `notes/literature/ArchPlanVQA_10_lines.md`
  - SHA-256：`f45a4a290c6912ddbff72dcfe19eeb1f4aa8bc1edeaf9b142d3dd076cbd3a076`
  - 说明：VLM/VQA 图纸理解对照任务参考。
- `notes/literature/HouseMind_10_lines.md`
  - SHA-256：`0876ebaa93667e1be381bbb2888469383702596f1635eb8232617789c52b337c`
  - 说明：MLLM/floor-plan tokenization 与 room/layout-level 边界。
- `notes/literature/TextEnhancedCAD_10_lines.md`
  - SHA-256：`c1f2c72c1bbac3c4a27e0a1f080ef6feff6d020211e91a9556dbc6ea77017d15`
  - 说明：文本增强 CAD spotting novelty 风险与 optional text stream 边界。
- `docs/drawingpt_v0_design_draft.md`
  - SHA-256：`87e2d5639e67d6865b7819c7eef1a40ff0f5bf86452e844dc6cab4073cf3bb3d`
  - 说明：DrawingPT v0 token 化、自监督目标和预训练语料估计草案。
- `docs/baseline_reproduction_plan.md`
  - SHA-256：`36c71e278facaca74f24b7e62f214ce3b3de9dd5e6a0fb00e1bfb50e25bd1715`
  - 说明：baseline 复现优先级与比较口径。

本周报收录判断：

- 收录：7 篇文献笔记如何转化为 DrawingPT 的 benchmark、baseline、自监督预训练、低标注曲线和 VLM/text 对照边界。
- 阶段边界：文献调研支持研究定位和实验设计，不作为模型性能已经提升的证据。

### 2.5 工程造价与 pseudo-BoQ 证据

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

### 2.6 CADTransformer 评估门禁证据

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
3. FloorPlanCAD 数据画像解释采样和评估风险，不替代模型效果证据。
4. 文献调研支持方法定位、baseline 选择和 novelty 边界，不替代实验结果。
5. CADTransformer 本期定位为 semantic baseline 与 PQ/SQ/RQ 评估链路审计；论文主指标走 official/proxy 门禁。
6. DrawingPT 预训练当前只支持 smoke 结论；有效性要等低标注曲线验证。
7. class-aware sampler 已经实现并完成 exposure audit，但它只证明采样分布被调整；模型效果仍需服务器 1000-step scratch/pretrained controlled run 对照。
8. 1000-step controlled run 已准备 Slurm 入口；未取得 Slurm summary 前只表述为正式实验计划/待提交门禁，不表述为完成结果。
9. 工程造价方向当前是文献定位和 pseudo-BoQ 中间层；真实造价模型需要后续 BoQ、单价、材料和造价标签。
10. GitHub 远端同步状态不进入组会正文。

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
