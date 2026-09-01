from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from drawingpt_v0_dataset import (
    FEATURE_NAMES,
    INPUT_TYPE_VOCAB_SIZE,
    MASK_TYPE_ID,
    PAD_TYPE_ID,
    PREDICT_TYPE_VOCAB_SIZE,
    FloorPlanCADPrimitiveDataset,
)


def require_torch():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torch.utils.data import DataLoader
    except Exception as exc:  # pragma: no cover - exercised on machines without torch.
        raise SystemExit(
            "PyTorch is required for training. On the server, activate the CADTransformer/DrawingPT torch environment; "
            "locally, use the Anaconda Python that already has torch if available. Original error: "
            + repr(exc)
        )
    return torch, nn, F, DataLoader


torch, nn, F, DataLoader = require_torch()


class MaskedPrimitiveModel(nn.Module):
    def __init__(
        self,
        feature_dim: int,
        input_type_vocab_size: int,
        predict_type_vocab_size: int,
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
        self.type_head = nn.Linear(hidden_dim, predict_type_vocab_size)
        self.feature_head = nn.Linear(hidden_dim, feature_dim)

    def forward(self, type_ids, features, attention_mask):
        batch_size, window_size = type_ids.shape
        positions = torch.arange(window_size, device=type_ids.device).unsqueeze(0).expand(batch_size, -1)
        hidden = self.type_embedding(type_ids) + self.feature_projection(features) + self.position_embedding(positions)
        padding_mask = ~attention_mask.bool()
        hidden = self.encoder(hidden, src_key_padding_mask=padding_mask)
        hidden = self.norm(hidden)
        return self.type_head(hidden), self.feature_head(hidden)


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


def apply_random_mask(type_ids, features, attention_mask, mask_ratio: float):
    valid = attention_mask.bool()
    random_values = torch.rand(type_ids.shape, device=type_ids.device)
    mask = (random_values < mask_ratio) & valid
    for row in range(mask.shape[0]):
        if valid[row].any() and not mask[row].any():
            valid_indices = torch.nonzero(valid[row], as_tuple=False).view(-1)
            pick = valid_indices[torch.randint(0, valid_indices.numel(), (1,), device=type_ids.device)]
            mask[row, pick] = True

    masked_type_ids = type_ids.clone()
    masked_features = features.clone()
    masked_type_ids[mask] = MASK_TYPE_ID
    masked_features[mask] = 0.0
    return masked_type_ids, masked_features, mask


def train(args) -> Dict[str, object]:
    set_seed(args.seed)
    device = choose_device(args.device)
    dataset = FloorPlanCADPrimitiveDataset(
        root=args.root,
        manifest_path=args.manifest,
        split=args.split,
        window_size=args.window_size,
        label_list_path=args.label_list,
        limit_files=args.limit_files,
        limit_windows=args.limit_windows,
    )
    if len(dataset) == 0:
        raise SystemExit("Dataset contains 0 windows. Check split, manifest, label-list, and root paths.")

    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        collate_fn=collate_batch,
        drop_last=False,
    )
    model = MaskedPrimitiveModel(
        feature_dim=dataset.feature_dim,
        input_type_vocab_size=INPUT_TYPE_VOCAB_SIZE,
        predict_type_vocab_size=PREDICT_TYPE_VOCAB_SIZE,
        window_size=args.window_size,
        hidden_dim=args.hidden_dim,
        layers=args.layers,
        heads=args.heads,
        dropout=args.dropout,
    ).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    started_at = time.time()
    losses: List[Dict[str, float]] = []
    step = 0
    model.train()
    while step < args.steps:
        for batch in loader:
            type_ids = batch["type_ids"].to(device)
            features = batch["features"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            masked_type_ids, masked_features, mask = apply_random_mask(
                type_ids=type_ids,
                features=features,
                attention_mask=attention_mask,
                mask_ratio=args.mask_ratio,
            )
            type_logits, feature_pred = model(masked_type_ids, masked_features, attention_mask)
            if not mask.any():
                continue
            type_loss = F.cross_entropy(type_logits[mask], type_ids[mask])
            feature_loss = F.smooth_l1_loss(feature_pred[mask], features[mask])
            loss = type_loss + args.feature_loss_weight * feature_loss

            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), args.grad_clip)
            optimizer.step()

            step += 1
            record = {
                "step": float(step),
                "loss": float(loss.detach().cpu().item()),
                "type_loss": float(type_loss.detach().cpu().item()),
                "feature_loss": float(feature_loss.detach().cpu().item()),
                "masked_tokens": float(mask.sum().detach().cpu().item()),
            }
            losses.append(record)
            if step == 1 or step % args.log_every == 0 or step == args.steps:
                print(
                    "step={step:d} loss={loss:.6f} type_loss={type_loss:.6f} "
                    "feature_loss={feature_loss:.6f} masked_tokens={masked_tokens:.0f}".format(
                        step=step,
                        loss=record["loss"],
                        type_loss=record["type_loss"],
                        feature_loss=record["feature_loss"],
                        masked_tokens=record["masked_tokens"],
                    ),
                    flush=True,
                )
            if step >= args.steps:
                break

    runtime_seconds = round(time.time() - started_at, 3)
    checkpoint_sha256 = None
    if args.checkpoint_out:
        args.checkpoint_out.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": model.state_dict(),
                "config": vars(args),
                "feature_names": FEATURE_NAMES,
                "input_type_vocab_size": INPUT_TYPE_VOCAB_SIZE,
                "predict_type_vocab_size": PREDICT_TYPE_VOCAB_SIZE,
            },
            args.checkpoint_out,
        )
        checkpoint_sha256 = sha256_file(args.checkpoint_out)

    summary = {
        "generated_at": "2026-09-01",
        "task": "masked primitive modeling smoke",
        "dataset_windows": len(dataset),
        "split": args.split,
        "label_list": str(args.label_list) if args.label_list else None,
        "window_size": args.window_size,
        "batch_size": args.batch_size,
        "steps": args.steps,
        "mask_ratio": args.mask_ratio,
        "hidden_dim": args.hidden_dim,
        "layers": args.layers,
        "heads": args.heads,
        "device": str(device),
        "torch_version": torch.__version__,
        "runtime_seconds": runtime_seconds,
        "first_loss": losses[0]["loss"] if losses else None,
        "last_loss": losses[-1]["loss"] if losses else None,
        "loss_history": losses,
        "checkpoint_out": str(args.checkpoint_out) if args.checkpoint_out else None,
        "checkpoint_sha256": checkpoint_sha256,
        "caveats": [
            "This is a smoke test for the self-supervised training loop, not a meaningful convergence result.",
            "The default local command is intentionally tiny and may run on CPU.",
            "Longer runs should use the server GPU with conservative Slurm resource requests.",
        ],
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a minimal DrawingPT v0 masked primitive model.")
    parser.add_argument("--root", type=Path, default=Path("data/raw/FloorPlanCAD"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("reports/next_steps_2026-09-01/floorplancad_token_manifest_by_file.csv"),
    )
    parser.add_argument("--split", choices=["train", "val", "test"], default="train")
    parser.add_argument("--label-list", type=Path, default=None)
    parser.add_argument("--window-size", type=int, default=512)
    parser.add_argument("--limit-files", type=int, default=0)
    parser.add_argument("--limit-windows", type=int, default=64)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--mask-ratio", type=float, default=0.30)
    parser.add_argument("--hidden-dim", type=int, default=64)
    parser.add_argument("--layers", type=int, default=2)
    parser.add_argument("--heads", type=int, default=4)
    parser.add_argument("--dropout", type=float, default=0.1)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--feature-loss-weight", type=float, default=1.0)
    parser.add_argument("--grad-clip", type=float, default=1.0)
    parser.add_argument("--seed", type=int, default=304)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--log-every", type=int, default=1)
    parser.add_argument("--summary-out", type=Path, default=Path("outputs/reports/drawingpt_v0_masked_smoke_summary.json"))
    parser.add_argument("--checkpoint-out", type=Path, default=Path("outputs/checkpoints/drawingpt_v0_masked_smoke.pt"))
    args = parser.parse_args()

    summary = train(args)
    text = json.dumps(summary, indent=2, ensure_ascii=False, default=str)
    print(text)
    if args.summary_out:
        args.summary_out.parent.mkdir(parents=True, exist_ok=True)
        args.summary_out.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
