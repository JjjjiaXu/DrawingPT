from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np

from drawingpt_v0_dataset import CLASS_NAMES, FloorPlanCADPrimitiveDataset, sha256_file
from train_semantic_primitive import (
    DEFAULT_RARE_CLASSES,
    NUM_SEMANTIC_CLASSES,
    build_class_aware_sample_weights,
    compute_supervised_class_counts,
)


def class_list(value: str) -> List[int]:
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def window_class_counts(dataset: FloorPlanCADPrimitiveDataset) -> List[collections.Counter[int]]:
    rows: List[collections.Counter[int]] = []
    for index in range(len(dataset)):
        item = dataset[index]
        labels = item["semantic_labels"]
        supervised = (labels >= 0) & (labels > 0)
        counts = collections.Counter(int(x) for x in labels[supervised].tolist())
        rows.append(counts)
    return rows


def summarize_epoch(
    sampled_indices: Iterable[int],
    per_window_counts: List[collections.Counter[int]],
    rare_classes: List[int],
) -> Dict[str, object]:
    sampled_indices = list(sampled_indices)
    total = collections.Counter()
    for index in sampled_indices:
        total.update(per_window_counts[index])
    fg_tokens = sum(total.values())
    top = total.most_common(10)
    rare_tokens = sum(total.get(class_id, 0) for class_id in rare_classes)
    supported_classes = [class_id for class_id in range(1, NUM_SEMANTIC_CLASSES) if total.get(class_id, 0) > 0]
    return {
        "sampled_windows": len(sampled_indices),
        "unique_windows": len(set(sampled_indices)),
        "foreground_tokens": fg_tokens,
        "classes_with_support": len(supported_classes),
        "rare_classes_with_support": sum(1 for class_id in rare_classes if total.get(class_id, 0) > 0),
        "rare_token_share": rare_tokens / fg_tokens if fg_tokens else 0.0,
        "wall_token_share": total.get(33, 0) / fg_tokens if fg_tokens else 0.0,
        "top10_classes": [
            {
                "class_id": class_id,
                "class_name": CLASS_NAMES.get(class_id, "<unknown>"),
                "tokens": count,
                "share": count / fg_tokens if fg_tokens else 0.0,
            }
            for class_id, count in top
        ],
    }


def write_markdown(summary: Dict[str, object], path: Path) -> None:
    random_epoch = summary["random_epoch"]
    class_aware_epoch = summary["class_aware_epoch"]
    sampler = summary["sampler"]
    lines = [
        "# DrawingPT v0 class-aware sampler audit",
        "",
        f"生成日期：{summary['generated_at']}",
        "",
        "## 一句话结论",
        "",
        "class-aware sampler 已经能在不增加 GPU 资源的前提下改变 1% 低标注训练窗口的暴露分布：它用 replacement 采样重复包含较少见前景类的窗口，用于对抗普通随机窗口被高频 wall/window/sink 主导的问题。",
        "",
        "## 设置",
        "",
        f"- split：{summary['split']}",
        f"- label list：`{summary['label_list']}`",
        f"- window size：{summary['window_size']}",
        f"- dataset windows：{summary['dataset_windows']}",
        f"- seed：{summary['seed']}",
        "",
        "## 一轮训练窗口暴露对比",
        "",
        "| sampler | sampled windows | unique windows | foreground tokens | classes with support | rare classes with support | rare token share | wall token share |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        "| random/no replacement | {sampled_windows} | {unique_windows} | {foreground_tokens} | {classes_with_support} | {rare_classes_with_support} | {rare_token_share:.4f} | {wall_token_share:.4f} |".format(
            **random_epoch
        ),
        "| class-aware/replacement | {sampled_windows} | {unique_windows} | {foreground_tokens} | {classes_with_support} | {rare_classes_with_support} | {rare_token_share:.4f} | {wall_token_share:.4f} |".format(
            **class_aware_epoch
        ),
        "",
        "## sampler 权重摘要",
        "",
        "| 指标 | 数值 |",
        "|---|---:|",
    ]
    for key, value in sampler["weight_summary"].items():
        lines.append(f"| {key} | {float(value):.6f} |")
    lines.extend(
        [
            "",
            "## 解释边界",
            "",
            "- 这是 sampler exposure audit，不是模型性能结果。",
            "- class-aware 采样会牺牲一部分 unique window 覆盖，换取少见类别窗口的重复暴露；后续必须和 validation macro/rare F1 一起看。",
            "- 如果某个极少类没有出现在 1% label-list 中，sampler 不能凭空创造该类监督信号，只能重分配已有监督窗口。",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit random vs class-aware DrawingPT v0 train-window exposure.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv"),
    )
    parser.add_argument("--label-list", type=Path, default=Path("configs/label_fractions/floorplancad_train_seed0304_001pct.txt"))
    parser.add_argument("--split", default="train")
    parser.add_argument("--window-size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=304)
    parser.add_argument("--rare-classes", default=",".join(str(x) for x in DEFAULT_RARE_CLASSES))
    parser.add_argument("--max-window-sample-weight", type=float, default=8.0)
    parser.add_argument("--summary-out", type=Path, default=Path("reports/next_steps_2026-09-01/drawingpt_v0_classaware_sampler_audit.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("reports/next_steps_2026-09-01/drawingpt_v0_classaware_sampler_audit.md"))
    args = parser.parse_args()

    rare_classes = class_list(args.rare_classes)
    dataset = FloorPlanCADPrimitiveDataset(
        root=args.root,
        manifest_path=args.manifest,
        split=args.split,
        window_size=args.window_size,
        label_list_path=args.label_list,
    )
    class_counts = compute_supervised_class_counts(dataset, include_background_in_loss=False)
    sample_weights, sampler_report = build_class_aware_sample_weights(
        dataset,
        class_counts,
        include_background_in_loss=False,
        max_window_sample_weight=args.max_window_sample_weight,
    )
    weights = sample_weights.detach().cpu().numpy().astype(np.float64)
    probs = weights / weights.sum()
    rng = np.random.default_rng(args.seed)
    class_aware_indices = rng.choice(np.arange(len(dataset)), size=len(dataset), replace=True, p=probs).tolist()
    random_indices = list(range(len(dataset)))
    per_window_counts = window_class_counts(dataset)

    summary: Dict[str, object] = {
        "generated_at": "2026-09-01",
        "task": "class-aware sampler exposure audit",
        "split": args.split,
        "label_list": str(args.label_list),
        "label_list_sha256": sha256_file(args.label_list),
        "manifest": str(args.manifest),
        "manifest_sha256": sha256_file(args.manifest),
        "window_size": args.window_size,
        "dataset_windows": len(dataset),
        "seed": args.seed,
        "rare_classes": rare_classes,
        "random_epoch": summarize_epoch(random_indices, per_window_counts, rare_classes),
        "class_aware_epoch": summarize_epoch(class_aware_indices, per_window_counts, rare_classes),
        "sampler": sampler_report,
        "caveats": [
            "This is a sampler exposure audit, not a model-quality result.",
            "Class-aware sampling cannot create supervision for classes absent from the low-label list.",
            "Replacement sampling may reduce unique-window coverage and must be validated with macro/rare F1.",
        ],
    }

    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(summary, args.markdown_out)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
