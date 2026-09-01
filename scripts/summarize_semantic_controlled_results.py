from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List


def load_summary(path: Path) -> Dict[str, object]:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def top_predictions(final_val: Dict[str, object], limit: int = 5) -> List[Dict[str, object]]:
    rows = final_val.get("per_class", [])
    return sorted(rows, key=lambda row: int(row.get("pred_count", 0)), reverse=True)[:limit]


def row_from_summary(path: Path, summary: Dict[str, object]) -> Dict[str, object]:
    final_val = summary.get("final_val", {})
    pretrain = summary.get("pretrained_encoder", {})
    sampler = summary.get("sampler", {})
    return {
        "file": str(path),
        "mode": summary.get("mode"),
        "pretrained": bool(pretrain.get("enabled")) if isinstance(pretrain, dict) else False,
        "sampler": sampler.get("method") if isinstance(sampler, dict) else None,
        "class_weighting": summary.get("class_weighting"),
        "steps": summary.get("steps"),
        "window_size": summary.get("window_size"),
        "train_dataset_windows": summary.get("train_dataset_windows"),
        "val_dataset_windows": summary.get("val_dataset_windows"),
        "runtime_seconds": summary.get("runtime_seconds"),
        "first_train_loss": summary.get("first_train_loss"),
        "last_train_loss": summary.get("last_train_loss"),
        "final_val_loss": final_val.get("loss") if isinstance(final_val, dict) else None,
        "final_accuracy_fg": final_val.get("accuracy_fg") if isinstance(final_val, dict) else None,
        "final_macro_f1_fg": final_val.get("macro_f1_fg") if isinstance(final_val, dict) else None,
        "final_rare_macro_f1": final_val.get("rare_macro_f1") if isinstance(final_val, dict) else None,
        "top_predictions": top_predictions(final_val) if isinstance(final_val, dict) else [],
        "checkpoint_sha256": summary.get("checkpoint_sha256"),
    }


def fmt(value, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def write_markdown(rows: List[Dict[str, object]], path: Path) -> None:
    lines = [
        "# DrawingPT v0 class-aware controlled semantic results",
        "",
        "## Controlled run table",
        "",
        "| run | pretrained | sampler | class weighting | steps | val windows | fg acc | macro F1 | rare F1 | runtime s |",
        "|---|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            "| {run} | {pretrained} | {sampler} | {class_weighting} | {steps} | {val_windows} | {fg_acc} | {macro_f1} | {rare_f1} | {runtime} |".format(
                run=Path(str(row["file"])).stem.replace("_summary", ""),
                pretrained="yes" if row["pretrained"] else "no",
                sampler=row["sampler"],
                class_weighting=row["class_weighting"],
                steps=row["steps"],
                val_windows=row["val_dataset_windows"],
                fg_acc=fmt(row["final_accuracy_fg"]),
                macro_f1=fmt(row["final_macro_f1_fg"]),
                rare_f1=fmt(row["final_rare_macro_f1"]),
                runtime=fmt(row["runtime_seconds"], 1),
            )
        )
    lines.extend(["", "## Interpretation notes", ""])
    lines.append("- 这些结果只在同一 seed、同一 label-list、同一 class-aware sampler 和同一验证设置下横向比较。")
    lines.append("- 若 macro F1 或 rare F1 没有改善，应优先检查 sampler coverage、class support 和 dominant predictions，而不是直接否定预训练。")
    lines.append("- 真实低标注结论至少需要 1%/5%/10% 和多个 seed。")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize DrawingPT v0 controlled semantic run JSON files.")
    parser.add_argument("summaries", nargs="+", type=Path)
    parser.add_argument("--json-out", type=Path, default=Path("reports/next_steps_2026-09-01/drawingpt_v0_classaware_controlled_results.json"))
    parser.add_argument("--markdown-out", type=Path, default=Path("reports/next_steps_2026-09-01/drawingpt_v0_classaware_controlled_results.md"))
    args = parser.parse_args()

    rows = [row_from_summary(path, load_summary(path)) for path in args.summaries]
    payload = {
        "generated_at": "2026-09-01",
        "task": "DrawingPT v0 class-aware controlled semantic result summary",
        "runs": rows,
    }
    args.json_out.parent.mkdir(parents=True, exist_ok=True)
    args.json_out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(rows, args.markdown_out)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
