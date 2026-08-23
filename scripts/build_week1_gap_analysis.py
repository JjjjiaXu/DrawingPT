from __future__ import annotations

import csv
import json
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "outputs" / "reports"
DOC_OUT = ROOT / "docs" / "floorplancad_distribution_report.md"
GROUP_DIR = ROOT / "reports" / "group_meeting_2026-08-18"

SPLITS = ("train", "val", "test")

COUNT_BINS = [
    ("0-99", 0, 99),
    ("100-499", 100, 499),
    ("500-999", 500, 999),
    ("1,000-1,999", 1000, 1999),
    ("2,000-4,999", 2000, 4999),
    ("5,000-9,999", 5000, 9999),
    ("10,000+", 10000, None),
]

PAPER_METRICS = [
    {
        "metric": "PQ",
        "paper_cadtransformer": "0.6732",
        "paper_cadtransformer_rl": "0.6894",
        "reproduction_job969": "未产出",
        "runtime": "10:21:28",
        "comparison_status": "不可直接比较",
        "reason": "本次没有跑 README 中的 panoptic quality 评估链路，日志里的 Total FG F1 不是 PQ。",
    },
    {
        "metric": "SQ",
        "paper_cadtransformer": "0.8754",
        "paper_cadtransformer_rl": "0.8832",
        "reproduction_job969": "未产出",
        "runtime": "10:21:28",
        "comparison_status": "不可直接比较",
        "reason": "SQ 是匹配符号的平均 IoU，本次训练日志没有输出该指标。",
    },
    {
        "metric": "RQ",
        "paper_cadtransformer": "0.7226",
        "paper_cadtransformer_rl": "0.7333",
        "reproduction_job969": "未产出",
        "runtime": "10:21:28",
        "comparison_status": "不可直接比较",
        "reason": "RQ 可理解为符号匹配层面的 F1，但不同于代码日志的 primitive-level Total FG F1。",
    },
    {
        "metric": "Total FG Precision",
        "paper_cadtransformer": "未报告",
        "paper_cadtransformer_rl": "未报告",
        "reproduction_job969": "0.832457",
        "runtime": "10:21:28",
        "comparison_status": "只可作为本次日志指标",
        "reason": "这是 CADTransformer eval.py 对前景 primitive 语义分类累计得到的 precision。",
    },
    {
        "metric": "Total FG Recall",
        "paper_cadtransformer": "未报告",
        "paper_cadtransformer_rl": "未报告",
        "reproduction_job969": "0.822702",
        "runtime": "10:21:28",
        "comparison_status": "只可作为本次日志指标",
        "reason": "这是 CADTransformer eval.py 对前景 primitive 语义分类累计得到的 recall。",
    },
    {
        "metric": "Total FG F1",
        "paper_cadtransformer": "未报告",
        "paper_cadtransformer_rl": "未报告",
        "reproduction_job969": "0.827501",
        "runtime": "10:21:28",
        "comparison_status": "不可冒充论文主指标",
        "reason": "可用于证明训练/验证链路跑通，但不能与论文 Table 1 的 PQ/SQ/RQ 直接相减。",
    },
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_file_counts(split: str) -> list[int]:
    path = REPORTS / f"floorplancad_{split}_file_stats.csv"
    counts: list[int] = []
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            counts.append(int(row["primitive_count"]))
    return counts


def fmt_int(value: int) -> str:
    return f"{value:,}"


def pct(value: int, total: int) -> str:
    if total == 0:
        return "0.00%"
    return f"{value / total * 100:.2f}%"


def describe(values: list[int]) -> dict[str, float | int]:
    values = sorted(values)
    if not values:
        return {}

    def percentile(q: float) -> int:
        idx = round((len(values) - 1) * q)
        return values[idx]

    return {
        "files": len(values),
        "min": min(values),
        "median": statistics.median(values),
        "mean": round(statistics.mean(values), 2),
        "p90": percentile(0.90),
        "p95": percentile(0.95),
        "p99": percentile(0.99),
        "max": max(values),
    }


def bin_counts(values: list[int]) -> dict[str, int]:
    out = {name: 0 for name, _, _ in COUNT_BINS}
    for value in values:
        for name, lo, hi in COUNT_BINS:
            if value >= lo and (hi is None or value <= hi):
                out[name] += 1
                break
    return out


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def main() -> None:
    stats = {split: load_json(REPORTS / f"floorplancad_{split}_stats.json") for split in SPLITS}
    primitive_counts = {split: read_file_counts(split) for split in SPLITS}
    all_counts = [value for split in SPLITS for value in primitive_counts[split]]

    tag_totals: dict[str, int] = {}
    split_tag_rows: list[dict[str, object]] = []
    for split in SPLITS:
        split_total = sum(stats[split]["tag_counts"].values())
        for tag, count in stats[split]["tag_counts"].items():
            tag_totals[tag] = tag_totals.get(tag, 0) + int(count)
            split_tag_rows.append(
                {
                    "split": split,
                    "tag": tag,
                    "count": count,
                    "share_in_split": f"{count / split_total:.6f}",
                }
            )

    all_tag_total = sum(tag_totals.values())
    tag_rows = [
        {
            "tag": tag,
            "count": count,
            "share": f"{count / all_tag_total:.6f}",
        }
        for tag, count in sorted(tag_totals.items(), key=lambda item: item[1], reverse=True)
    ]
    write_csv(GROUP_DIR / "floorplancad_tag_distribution.csv", tag_rows, ["tag", "count", "share"])

    primitive_bin_rows: list[dict[str, object]] = []
    for split in (*SPLITS, "all"):
        values = all_counts if split == "all" else primitive_counts[split]
        bins = bin_counts(values)
        total = len(values)
        for name, count in bins.items():
            primitive_bin_rows.append(
                {
                    "split": split,
                    "primitive_count_bin": name,
                    "file_count": count,
                    "share": f"{count / total:.6f}",
                }
            )
    write_csv(
        GROUP_DIR / "floorplancad_primitive_count_bins.csv",
        primitive_bin_rows,
        ["split", "primitive_count_bin", "file_count", "share"],
    )

    semantic_totals: dict[int, dict[str, object]] = {}
    split_coverage = {split: set() for split in SPLITS}
    for split in SPLITS:
        for class_id_text, item in stats[split]["semantic_counts"].items():
            class_id = int(class_id_text)
            split_coverage[split].add(class_id)
            if class_id not in semantic_totals:
                semantic_totals[class_id] = {"name": item["name"], "count": 0, "splits": set()}
            semantic_totals[class_id]["count"] = int(semantic_totals[class_id]["count"]) + int(item["count"])
            semantic_totals[class_id]["splits"].add(split)

    total_semantic = sum(int(item["count"]) for item in semantic_totals.values())
    semantic_rows = []
    for class_id, item in sorted(semantic_totals.items(), key=lambda entry: int(entry[1]["count"]), reverse=True):
        semantic_rows.append(
            {
                "class_id": class_id,
                "class_name": item["name"],
                "count": item["count"],
                "share": f"{int(item['count']) / total_semantic:.6f}",
                "split_coverage": "+".join(sorted(item["splits"])),
            }
        )
    write_csv(
        GROUP_DIR / "floorplancad_semantic_distribution.csv",
        semantic_rows,
        ["class_id", "class_name", "count", "share", "split_coverage"],
    )

    write_csv(
        GROUP_DIR / "cadtransformer_metric_comparison.csv",
        PAPER_METRICS,
        [
            "metric",
            "paper_cadtransformer",
            "paper_cadtransformer_rl",
            "reproduction_job969",
            "runtime",
            "comparison_status",
            "reason",
        ],
    )

    all_desc = describe(all_counts)
    split_desc_rows = []
    for split in SPLITS:
        item = stats[split]
        desc = describe(primitive_counts[split])
        split_desc_rows.append(
            [
                split,
                fmt_int(item["file_count"]),
                fmt_int(sum(item["tag_counts"].values())),
                fmt_int(int(desc["median"])),
                f"{desc['mean']:.2f}",
                fmt_int(int(desc["p95"])),
                fmt_int(int(desc["max"])),
                f"{item['instance_count_per_file']['mean']:.2f}",
            ]
        )

    tag_table_rows = [
        [row["tag"], fmt_int(int(row["count"])), f"{float(row['share']) * 100:.2f}%"]
        for row in tag_rows
    ]
    top_semantic_rows = [
        [
            str(row["class_id"]),
            str(row["class_name"]),
            fmt_int(int(row["count"])),
            f"{float(row['share']) * 100:.2f}%",
            str(row["split_coverage"]),
        ]
        for row in semantic_rows[:15]
    ]
    rare_semantic_rows = [
        [
            str(row["class_id"]),
            str(row["class_name"]),
            fmt_int(int(row["count"])),
            f"{float(row['share']) * 100:.4f}%",
            str(row["split_coverage"]),
        ]
        for row in semantic_rows[-10:]
    ]
    bin_table_rows = []
    all_bins = {row["primitive_count_bin"]: row for row in primitive_bin_rows if row["split"] == "all"}
    for name, _, _ in COUNT_BINS:
        row = all_bins[name]
        bin_table_rows.append(
            [
                name,
                fmt_int(int(row["file_count"])),
                f"{float(row['share']) * 100:.2f}%",
            ]
        )

    metric_rows = [
        [
            row["metric"],
            row["paper_cadtransformer"],
            row["paper_cadtransformer_rl"],
            row["reproduction_job969"],
            row["runtime"],
            row["comparison_status"],
        ]
        for row in PAPER_METRICS
    ]

    doc = f"""# FloorPlanCAD 图元分布与 CADTransformer 指标差距检查

生成日期：2026-08-23

本报告补齐第一周 checklist 中两项容易被追问的内容：

1. FloorPlanCAD 的图元类型、每图图元数量分布、35 类语义标注数量分布。
2. CADTransformer 论文指标 vs 本次复现指标 vs runtime，以及“差距超过 2 个点要找原因”的当前结论。

## 1. 数据统计口径

- 数据版本：当前仓库本地使用的是 CADTransformer / SymPoint / GAT-CADNet 公开脚本对应的 FloorPlanCAD 11,602 张版本。
- 统计对象：`train/train/svg_gt`、`val/val/svg_gt`、`test/test/svg_gt` 下的 SVG。
- raw SVG 图元类型统计：只统计实际出现的 SVG primitive tag，包括 `path`、`circle`、`ellipse`。
- 语义类别统计：统计带 `semanticId` 的 SVG 元素；它不是所有 raw SVG 图元的总数。
- instance 统计：只统计 `instanceId >= 0` 的实例，`-1` 视为 stuff/background-like 标注。

## 2. 每个 split 的图元数量分布

全量共有 {fmt_int(int(all_desc["files"]))} 张图，raw SVG primitive 共 {fmt_int(all_tag_total)} 个。单图 primitive 数的中位数为 {fmt_int(int(all_desc["median"]))}，均值为 {all_desc["mean"]:.2f}，p95 为 {fmt_int(int(all_desc["p95"]))}，最大值为 {fmt_int(int(all_desc["max"]))}。

{markdown_table(
        ["split", "SVG 文件数", "raw primitive 总数", "单图中位数", "单图均值", "单图 p95", "单图最大值", "instance 均值"],
        split_desc_rows,
    )}

## 3. SVG 图元类型分布

`path` 占绝对多数，说明 FloorPlanCAD 虽然是 SVG 矢量格式，但对模型而言主要还是大量路径片段，圆和椭圆只占很小比例。

{markdown_table(["SVG tag", "数量", "占 raw primitive 比例"], tag_table_rows)}

## 4. 每张图的 raw primitive 数量桶

这个分布解释了为什么 baseline 训练容易遇到显存/时间问题：大多数图在 500-1,999 个 primitive 之间，但存在超过 10,000 primitive 的长尾大图。

{markdown_table(["单图 raw primitive 数", "SVG 文件数", "占比"], bin_table_rows)}

## 5. 语义标注数量分布

全量带 `semanticId` 的元素共 {fmt_int(total_semantic)} 个，35 类在全量 train+val+test 中全部出现。注意 val split 只覆盖 33/35 类，缺少极少见的 revolving door 和 rolling door；因此小验证集上的 rare-class 波动会很大。

### Top 15 类

{markdown_table(["class id", "类别", "带 semanticId 元素数", "占语义标注比例", "出现 split"], top_semantic_rows)}

### 最少 10 类

{markdown_table(["class id", "类别", "带 semanticId 元素数", "占语义标注比例", "出现 split"], rare_semantic_rows)}

## 6. CADTransformer 论文指标 vs 本次复现指标 vs runtime

CADTransformer 原论文 Table 1 的主指标是 panoptic symbol spotting 的 PQ/SQ/RQ；本次 job 969 日志冻结的是 `eval.py` 输出的前景 primitive 语义 Total FG Precision/Recall/F1。这两组不是同一口径，不能直接相减。

论文数值来源：CVPR 2022 论文 *CADTransformer: Panoptic Symbol Spotting Transformer for CAD Drawings* 的 Table 1。评估链路来源：官方 GitHub README 中的 `scripts/evaluate_pq.py` 说明。

{markdown_table(
        ["指标", "论文 CADTransformer", "论文 CADTransformer+RL", "本次 job 969", "本次 runtime", "当前可比性"],
        metric_rows,
    )}

## 7. “差距超过 2 个点要找原因”的当前结论

当前还不能计算严格的论文差距，因为本次没有产出论文主表所需的 PQ/SQ/RQ。这里的主要问题不是“差了几个点”，而是“指标口径还没对齐”。这本身就应该被记录为未过门禁项。

如果后续恢复 paper-faithful 配置并跑出 PQ/SQ/RQ，只要任一主指标与论文 CADTransformer+RL 差距超过 0.02 absolute，就按下面顺序排查：

1. **指标口径**：是否真的跑了 `evaluate_pq.py` 对应的 panoptic quality，而不是训练日志里的 Total FG F1。
2. **训练配置**：论文是 40 epochs、4 张 RTX A6000、HRNet 和 ViT backbone 预训练并 joint fine-tune；本次 job 969 是 10 epochs、1 张 RTX 5090、`img_size=384`、`rgb_dim=0`。
3. **输入特征**：本次没有生成/使用 `npy_rgb`，因此跳过 RGB feature 分支。
4. **数据版本与预处理**：当前是 11,602 张公开脚本版本；后续必须确认与论文 first version / 官方版本是否完全一致。
5. **增强策略**：论文最优行使用 Random Layer augmentation，本次未对齐。
6. **环境兼容补丁**：本次为了 Python 3.11、NumPy 1.26、timm 0.6.13 做过兼容补丁，paper-faithful 复现前要确认补丁没有改变模型语义。

## 8. 结论

这两项 checklist 现在的完成状态应写成：

- FloorPlanCAD 图元类型/数量分布：**已补齐**，并有可复用 CSV 摘要。
- 论文指标 vs 复现指标 vs runtime：**已补齐比较表，但 paper-faithful 指标尚未产出**；当前差距原因首先是指标和实验协议未对齐，而不是模型性能结论。

## 9. 公开来源

- CADTransformer CVPR 2022 论文：https://openaccess.thecvf.com/content/CVPR2022/papers/Fan_CADTransformer_Panoptic_Symbol_Spotting_Transformer_for_CAD_Drawings_CVPR_2022_paper.pdf
- CADTransformer 官方实现：https://github.com/VITA-Group/CADTransformer
- FloorPlanCAD 官网：https://floorplancad.github.io/

"""

    DOC_OUT.write_text(doc.rstrip() + "\n", encoding="utf-8")
    print(f"wrote {DOC_OUT.relative_to(ROOT)}")
    print(f"wrote {GROUP_DIR.relative_to(ROOT)}/*.csv")


if __name__ == "__main__":
    main()
