from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from drawingpt_v0_dataset import (
    CLASS_NAMES,
    FEATURE_NAMES,
    INPUT_TYPE_VOCAB_SIZE,
    PAD_TYPE_ID,
    FloorPlanCADPrimitiveDataset,
)


NUM_SEMANTIC_CLASSES = 36  # 0 = background/unlabeled, 1..35 = FloorPlanCAD classes.
DEFAULT_RARE_CLASSES = [5, 6, 8, 9, 10, 15, 21, 23, 26, 30, 31, 34, 35]


def require_torch():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torch.utils.data import DataLoader
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "PyTorch is required for semantic fine-tuning. Activate the server torch environment "
            "or use a local Python with torch installed. Original error: " + repr(exc)
        )
    return torch, nn, F, DataLoader


torch, nn, F, DataLoader = require_torch()


class SemanticPrimitiveModel(nn.Module):
    def __init__(
        self,
        feature_dim: int,
        input_type_vocab_size: int,
        num_classes: int,
        window_size: int,
        hidden_dim: int = 128,
        layers: int = 2,
        heads: int = 4,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.type_embedding = nn.Embedding(input_type_vocab_size, hidden_dim, padding_idx=PAD_TYPE_ID)
        self.feature_projection = nn.Linear(feature_dim, hidden_dim)
        self.position_embedding = nn.Embedding(window_size, hidden_dim)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim,
            nhead=heads,
            dim_feedforward=hidden_dim * 4,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=layers)
        self.norm = nn.LayerNorm(hidden_dim)
        self.semantic_head = nn.Linear(hidden_dim, num_classes)

    def forward(self, type_ids, features, attention_mask):
        batch_size, window_size = type_ids.shape
        positions = torch.arange(window_size, device=type_ids.device).unsqueeze(0).expand(batch_size, -1)
        hidden = self.type_embedding(type_ids) + self.feature_projection(features) + self.position_embedding(positions)
        padding_mask = ~attention_mask.bool()
        hidden = self.encoder(hidden, src_key_padding_mask=padding_mask)
        hidden = self.norm(hidden)
        return self.semantic_head(hidden)


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collate_batch(items: List[Dict[str, object]]) -> Dict[str, object]:
    return {
        "features": torch.from_numpy(np.stack([item["features"] for item in items])).float(),
        "type_ids": torch.from_numpy(np.stack([item["type_ids"] for item in items])).long(),
        "semantic_labels": torch.from_numpy(np.stack([item["semantic_labels"] for item in items])).long(),
        "attention_mask": torch.from_numpy(np.stack([item["attention_mask"] for item in items])).bool(),
        "files": [item["file"] for item in items],
        "window_indices": [item["window_index"] for item in items],
    }


def choose_device(device_arg: str):
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def parse_class_list(value: str) -> List[int]:
    if not value:
        return DEFAULT_RARE_CLASSES[:]
    return [int(part.strip()) for part in value.split(",") if part.strip()]


def load_pretrained_encoder(model: SemanticPrimitiveModel, checkpoint_path: Optional[Path]) -> Dict[str, object]:
    if checkpoint_path is None:
        return {"enabled": False}
    if not checkpoint_path.exists():
        raise FileNotFoundError(str(checkpoint_path))

    checkpoint = torch.load(str(checkpoint_path), map_location="cpu")
    state = checkpoint.get("model_state_dict", checkpoint)
    current = model.state_dict()
    compatible = {}
    skipped = []
    for key, value in state.items():
        if key in current and tuple(current[key].shape) == tuple(value.shape):
            compatible[key] = value
        else:
            skipped.append(key)
    missing, unexpected = model.load_state_dict(compatible, strict=False)
    return {
        "enabled": True,
        "checkpoint": str(checkpoint_path),
        "checkpoint_sha256": sha256_file(checkpoint_path),
        "loaded_key_count": len(compatible),
        "skipped_key_count": len(skipped),
        "skipped_keys": skipped[:20],
        "missing_keys": list(missing)[:20],
        "unexpected_keys": list(unexpected)[:20],
    }


def empty_metrics() -> Dict[str, object]:
    return {
        "loss": None,
        "token_count_all": 0,
        "token_count_fg": 0,
        "accuracy_all": None,
        "accuracy_fg": None,
        "macro_f1_fg": None,
        "rare_macro_f1": None,
        "per_class": [],
    }


def compute_metrics(
    logits_list: List[torch.Tensor],
    labels_list: List[torch.Tensor],
    loss_values: List[float],
    rare_classes: List[int],
) -> Dict[str, object]:
    if not logits_list:
        return empty_metrics()

    logits = torch.cat(logits_list, dim=0)
    labels = torch.cat(labels_list, dim=0)
    valid = labels >= 0
    if not valid.any():
        return empty_metrics()

    preds = logits.argmax(dim=-1)
    labels_valid = labels[valid]
    preds_valid = preds[valid]
    fg = labels_valid > 0
    correct_all = (preds_valid == labels_valid).sum().item()
    accuracy_all = correct_all / max(int(labels_valid.numel()), 1)
    if fg.any():
        correct_fg = (preds_valid[fg] == labels_valid[fg]).sum().item()
        accuracy_fg = correct_fg / max(int(fg.sum().item()), 1)
    else:
        accuracy_fg = None

    per_class = []
    f1_values = []
    rare_f1_values = []
    for class_id in range(1, NUM_SEMANTIC_CLASSES):
        pred_pos = preds_valid == class_id
        true_pos = labels_valid == class_id
        support = int(true_pos.sum().item())
        pred_count = int(pred_pos.sum().item())
        if support == 0 and pred_count == 0:
            continue
        tp = int((pred_pos & true_pos).sum().item())
        precision = tp / pred_count if pred_count else 0.0
        recall = tp / support if support else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        row = {
            "class_id": class_id,
            "class_name": CLASS_NAMES.get(class_id, "<unknown>"),
            "support": support,
            "pred_count": pred_count,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
        per_class.append(row)
        if support > 0:
            f1_values.append(f1)
            if class_id in rare_classes:
                rare_f1_values.append(f1)

    return {
        "loss": float(sum(loss_values) / len(loss_values)) if loss_values else None,
        "token_count_all": int(labels_valid.numel()),
        "token_count_fg": int(fg.sum().item()),
        "accuracy_all": accuracy_all,
        "accuracy_fg": accuracy_fg,
        "macro_f1_fg": float(sum(f1_values) / len(f1_values)) if f1_values else None,
        "rare_macro_f1": float(sum(rare_f1_values) / len(rare_f1_values)) if rare_f1_values else None,
        "rare_classes": rare_classes,
        "per_class": per_class,
    }


def supervised_mask(labels: torch.Tensor, include_background_in_loss: bool) -> torch.Tensor:
    valid = labels >= 0
    if include_background_in_loss:
        return valid
    return valid & (labels > 0)


def evaluate(
    model,
    loader,
    device,
    max_batches: int,
    rare_classes: List[int],
    include_background_in_loss: bool,
) -> Dict[str, object]:
    model.eval()
    logits_list: List[torch.Tensor] = []
    labels_list: List[torch.Tensor] = []
    loss_values: List[float] = []
    with torch.no_grad():
        for batch_index, batch in enumerate(loader):
            if max_batches and batch_index >= max_batches:
                break
            type_ids = batch["type_ids"].to(device)
            features = batch["features"].to(device)
            labels = batch["semantic_labels"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(type_ids, features, attention_mask)
            valid = labels >= 0
            supervised = supervised_mask(labels, include_background_in_loss)
            if valid.any():
                logits_list.append(logits[valid].detach().cpu())
                labels_list.append(labels[valid].detach().cpu())
            if supervised.any():
                loss = F.cross_entropy(logits[supervised], labels[supervised])
                loss_values.append(float(loss.detach().cpu().item()))
    model.train()
    return compute_metrics(logits_list, labels_list, loss_values, rare_classes)


def train(args) -> Dict[str, object]:
    set_seed(args.seed)
    device = choose_device(args.device)
    rare_classes = parse_class_list(args.rare_classes)

    train_dataset = FloorPlanCADPrimitiveDataset(
        root=args.root,
        manifest_path=args.manifest,
        split="train",
        window_size=args.window_size,
        label_list_path=args.label_list,
        limit_files=args.limit_files,
        limit_windows=args.limit_windows,
    )
    val_dataset = FloorPlanCADPrimitiveDataset(
        root=args.root,
        manifest_path=args.manifest,
        split="val",
        window_size=args.window_size,
        label_list_path=None,
        limit_files=args.val_limit_files,
        limit_windows=args.val_limit_windows,
    )
    if len(train_dataset) == 0:
        raise SystemExit("Train dataset contains 0 windows. Check root, manifest, label-list, and window size.")

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_batch,
        drop_last=False,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=args.eval_batch_size,
        shuffle=False,
        num_workers=args.num_workers,
        collate_fn=collate_batch,
        drop_last=False,
    )

    model = SemanticPrimitiveModel(
        feature_dim=train_dataset.feature_dim,
        input_type_vocab_size=INPUT_TYPE_VOCAB_SIZE,
        num_classes=NUM_SEMANTIC_CLASSES,
        window_size=args.window_size,
        hidden_dim=args.hidden_dim,
        layers=args.layers,
        heads=args.heads,
        dropout=args.dropout,
    ).to(device)
    pretrain_report = load_pretrained_encoder(model, args.pretrained_checkpoint)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    initial_val = (
        evaluate(model, val_loader, device, args.eval_batches, rare_classes, args.include_background_in_loss)
        if len(val_dataset)
        else empty_metrics()
    )

    started_at = time.time()
    train_losses: List[Dict[str, float]] = []
    step = 0
    model.train()
    while step < args.steps:
        for batch in train_loader:
            type_ids = batch["type_ids"].to(device)
            features = batch["features"].to(device)
            labels = batch["semantic_labels"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            logits = model(type_ids, features, attention_mask)
            valid = labels >= 0
            supervised = supervised_mask(labels, args.include_background_in_loss)
            if not supervised.any():
                continue
            loss = F.cross_entropy(logits[supervised], labels[supervised])

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()

            step += 1
            record = {
                "step": float(step),
                "loss": float(loss.detach().cpu().item()),
                "tokens": float(supervised.sum().item()),
                "valid_tokens": float(valid.sum().item()),
                "foreground_tokens": float((valid & (labels > 0)).sum().item()),
            }
            train_losses.append(record)
            if step == 1 or step % args.log_every == 0 or step == args.steps:
                print(
                    "step={step:d} loss={loss:.6f} supervised_tokens={tokens:.0f}".format(
                        step=step, loss=record["loss"], tokens=record["tokens"]
                    ),
                    flush=True,
                )
            if step >= args.steps:
                break

    final_val = (
        evaluate(model, val_loader, device, args.eval_batches, rare_classes, args.include_background_in_loss)
        if len(val_dataset)
        else empty_metrics()
    )
    runtime_seconds = round(time.time() - started_at, 3)

    checkpoint_sha256 = None
    if args.checkpoint_out:
        args.checkpoint_out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "config": vars(args),
                "feature_names": FEATURE_NAMES,
                "num_semantic_classes": NUM_SEMANTIC_CLASSES,
                "pretrained_encoder": pretrain_report,
            },
            args.checkpoint_out,
        )
        checkpoint_sha256 = sha256_file(args.checkpoint_out)

    summary = {
        "generated_at": "2026-09-01",
        "task": "semantic primitive classification smoke",
        "mode": "pretrained_finetune" if args.pretrained_checkpoint else "scratch",
        "split": "train",
        "label_list": str(args.label_list) if args.label_list else None,
        "train_dataset_windows": len(train_dataset),
        "val_dataset_windows": len(val_dataset),
        "window_size": args.window_size,
        "batch_size": args.batch_size,
        "eval_batch_size": args.eval_batch_size,
        "steps": args.steps,
        "hidden_dim": args.hidden_dim,
        "layers": args.layers,
        "heads": args.heads,
        "device": str(device),
        "torch_version": torch.__version__,
        "loss_target": "all_valid_tokens_including_background"
        if args.include_background_in_loss
        else "foreground_semantic_ids_1_to_35",
        "runtime_seconds": runtime_seconds,
        "first_train_loss": train_losses[0]["loss"] if train_losses else None,
        "last_train_loss": train_losses[-1]["loss"] if train_losses else None,
        "train_loss_history": train_losses,
        "initial_val": initial_val,
        "final_val": final_val,
        "pretrained_encoder": pretrain_report,
        "checkpoint_out": str(args.checkpoint_out) if args.checkpoint_out else None,
        "checkpoint_sha256": checkpoint_sha256,
        "caveats": [
            "This is a semantic fine-tuning smoke/baseline, not a paper-quality result.",
            "The classifier predicts 0=background/unlabeled plus FloorPlanCAD semantic IDs 1..35.",
            "By default the training loss ignores class 0 to avoid a trivial background-only shortcut.",
            "Macro/rare F1 are only meaningful when the validation window subset has enough class support.",
        ],
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a minimal DrawingPT v0 semantic primitive classifier.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv"),
    )
    parser.add_argument("--label-list", type=Path, default=Path("configs/label_fractions/floorplancad_train_seed0304_001pct.txt"))
    parser.add_argument("--window-size", type=int, default=512)
    parser.add_argument("--limit-files", type=int, default=0)
    parser.add_argument("--limit-windows", type=int, default=64)
    parser.add_argument("--val-limit-files", type=int, default=0)
    parser.add_argument("--val-limit-windows", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--eval-batch-size", type=int, default=4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--eval-batches", type=int, default=16)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=304)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--log-every", type=int, default=1)
    parser.add_argument("--rare-classes", default=",".join(str(x) for x in DEFAULT_RARE_CLASSES))
    parser.add_argument("--pretrained-checkpoint", type=Path, default=None)
    parser.add_argument(
        "--include-background-in-loss",
        action="store_true",
        help="Also supervise semantic class 0. Default is to ignore class 0 and train only on semantic IDs 1..35.",
    )
    parser.add_argument("--summary-out", type=Path, default=Path("outputs/reports/drawingpt_v0_semantic_scratch_smoke_summary.json"))
    parser.add_argument("--checkpoint-out", type=Path, default=Path("outputs/checkpoints/drawingpt_v0_semantic_scratch_smoke.pt"))
    args = parser.parse_args()

    summary = train(args)
    text = json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    print(text)
    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
