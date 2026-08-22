from __future__ import annotations

from pathlib import Path


def replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        print(f"patched {path}: {old!r} -> {new!r}")


def ensure_contains(path: Path, needle: str, insert_after: str, insertion: str) -> None:
    text = path.read_text(encoding="utf-8")
    if needle in text:
        return
    if insert_after not in text:
        raise RuntimeError(f"Cannot patch {path}; marker not found: {insert_after!r}")
    path.write_text(text.replace(insert_after, insert_after + insertion), encoding="utf-8")
    print(f"patched {path}: inserted {needle!r}")


def ensure_line_after_imports(path: Path, line: str) -> None:
    text = path.read_text(encoding="utf-8")
    if line in text:
        return
    lines = text.splitlines()
    insert_at = 0
    for i, current in enumerate(lines):
        if current.startswith("import ") or current.startswith("from "):
            insert_at = i + 1
    lines.insert(insert_at, line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"patched {path}: added {line!r}")


def main() -> None:
    repo = Path(__file__).resolve().parents[2] / "third_party" / "CADTransformer"
    if not repo.exists():
        raise SystemExit(f"CADTransformer not found: {repo}")

    # Release scripts import _utils_dataset, but this checkout ships utils_dataset.py.
    src = repo / "preprocess" / "utils_dataset.py"
    dst = repo / "preprocess" / "_utils_dataset.py"
    if src.exists() and not dst.exists():
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"created {dst}")
    for helper in [src, dst]:
        if helper.exists():
            ensure_line_after_imports(helper, "import signal")
            ensure_line_after_imports(helper, "import cairosvg")
            replace(
                helper,
                '    # cairosvg.svg2png(url=svg_path, write_to=png_path, background_color="white")\n'
                '    command = "cairosvg {} -o {} -b {} -s {}".format(svg_path, png_path, background_color, scale)\n'
                "    os.system(command)",
                "    cairosvg.svg2png(url=svg_path, write_to=png_path, "
                "background_color=background_color, scale=scale)",
            )

    # numpy >= 1.24 removed aliases such as np.long and np.int. Keep code
    # compatible with modern server stacks while preserving integer semantics.
    for path in [repo / "dataset.py", repo / "models" / "model.py"]:
        replace(path, "dtype=np.long", "dtype=np.int64")
    replace(
        repo / "models" / "seg_hrnet.py",
        "last_inp_channels = np.int(np.sum(pre_stage_channels))",
        "last_inp_channels = int(np.sum(pre_stage_channels))",
    )

    # timm 0.6.x exposes init_weights_vit_timm instead of the older
    # _init_vit_weights symbol expected by this CADTransformer release. Keep
    # the old call sites working by defining a small compatibility wrapper.
    vit = repo / "models" / "vit.py"
    replace(
        vit,
        "from timm.models.vision_transformer import VisionTransformer, _create_vision_transformer, "
        "_init_vit_weights, checkpoint_filter_fn, default_cfgs",
        "from timm.models.vision_transformer import VisionTransformer, _create_vision_transformer, "
        "checkpoint_filter_fn, default_cfgs\n"
        "try:\n"
        "    from timm.models.vision_transformer import _init_vit_weights\n"
        "except ImportError:\n"
        "    from timm.models.vision_transformer import init_weights_vit_timm as _timm_init_weights\n"
        "\n"
        "    def _init_vit_weights(module, name='', head_bias=0., jax_impl=False):\n"
        "        return _timm_init_weights(module, name=name)",
    )
    replace(
        vit,
        "try:\n"
        "    from timm.models.vision_transformer import _init_vit_weights\n"
        "except ImportError:\n"
        "    from timm.models.vision_transformer import init_weights_vit_timm as _timm_init_weights\n"
        "\n"
        "    def _init_vit_weights(module, name='', head_bias=0., jax_impl=False):\n"
        "        return _timm_init_weights(module, name=name)",
        "try:\n"
        "    from timm.models.vision_transformer import _init_vit_weights\n"
        "except ImportError:\n"
        "    def _init_vit_weights(module, name='', head_bias=0., jax_impl=False):\n"
        "        if isinstance(module, nn.Linear):\n"
        "            trunc_normal_(module.weight, std=.02)\n"
        "            if module.bias is not None:\n"
        "                nn.init.constant_(module.bias, head_bias if name and name.startswith('head') else 0)\n"
        "        elif isinstance(module, nn.LayerNorm):\n"
        "            if module.bias is not None:\n"
        "                nn.init.zeros_(module.bias)\n"
        "            if module.weight is not None:\n"
        "                nn.init.ones_(module.weight)\n"
        "        elif isinstance(module, nn.Conv2d):\n"
        "            lecun_normal_(module.weight)\n"
        "            if module.bias is not None:\n"
        "                nn.init.zeros_(module.bias)",
    )
    replace(
        vit,
        "act_layer=None, weight_init='', out_indices=[], model_nn=None, model_k=None):",
        "act_layer=None, weight_init='', out_indices=[], model_nn=None, model_k=None, **kwargs):",
    )
    replace(
        vit,
        "class VisionTransformer_(VisionTransformer):",
        "class VisionTransformer_(nn.Module):",
    )
    replace(
        repo / "models" / "model.py",
        "        self.transformers = get_vit(pretrained=True, cfg=cfg)",
        "        vit_pretrained = os.environ.get(\"CADTRANSFORMER_VIT_PRETRAINED\", \"1\").lower() "
        "not in {\"0\", \"false\", \"no\"}\n"
        "        self.transformers = get_vit(pretrained=vit_pretrained, cfg=cfg)",
    )

    # torchrun sets LOCAL_RANK in the environment; old launch injected --local_rank.
    train = repo / "train_cad_ddp.py"
    ensure_contains(
        train,
        "default=int(os.environ.get(\"LOCAL_RANK\", 0))",
        "parser.add_argument(\"--local_rank\", type=int, default=0)",
        "\n    args_default_local_rank = int(os.environ.get(\"LOCAL_RANK\", 0))",
    )
    text = train.read_text(encoding="utf-8")
    text = text.replace(
        "parser.add_argument(\"--local_rank\", type=int, default=0)",
        "parser.add_argument(\"--local_rank\", type=int, default=int(os.environ.get(\"LOCAL_RANK\", 0)))",
    )
    # Clean up the harmless insertion if this patch is rerun after replacement.
    text = text.replace("\n    args_default_local_rank = int(os.environ.get(\"LOCAL_RANK\", 0))", "")
    train.write_text(text, encoding="utf-8")
    print("CADTransformer compatibility patch complete.")


if __name__ == "__main__":
    main()
