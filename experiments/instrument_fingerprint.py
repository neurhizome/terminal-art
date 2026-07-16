#!/usr/bin/env python3
"""The Instrument's Fingerprint — white noise, read closely.

Session 010 experiment. The J-lens (homelab/lens) transports each layer's
residual toward the output basis via a mean Jacobian J̄. Calibration
(2026-07-15) showed layers 6–12 collapse to effective rank 13–29 of 1536.

This piece renders what that collapse LOOKS like: the same 100 random unit
directions — residual-space white light, no text, no mind — decoded through
every layer's transport. One row per layer, one column per direction.
Glyph + color = the decoded top-1 token (hash → hue), so identical decodes
form visible runs. At healthy layers white light decodes as confetti; at
collapsed layers it decodes as stripes of the same few tokens. Order out of
noise is the artifact. The confetti is the truth.

Inverts the usual asciicology aesthetic: every other session hunts emergent
order in noise and celebrates finding it. Here order is the failure mode.

Usage:  uv run --project ~/homelab/lens python instrument_fingerprint.py \
            [--cols 100] [--out capture.ans]
Reads:  /mnt/checkpoints/lens/gemma4-e2b/lenses/{lens.pt,calibration.json}
        + the gemma4-e2b unembedding (HF cache). CPU, ~1 min.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import sys

import torch
from safetensors import safe_open
from transformers import AutoTokenizer

DEFAULT_LENSES = "/mnt/checkpoints/lens/gemma4-e2b/lenses"
SNAP = sorted(glob.glob(
    "/home/dusty/.cache/huggingface/hub/models--google--gemma-4-e2b-it"
    "/snapshots/*/model.safetensors"))[0]

RESET = "\x1b[0m"


def hue_for(token_id: int) -> int:
    """Stable 256-color for a vocab id (avoid the dark 16..27 band)."""
    h = int(hashlib.md5(str(token_id).encode()).hexdigest(), 16)
    return 28 + h % 200


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cols", type=int, default=100)
    ap.add_argument("--out", default=None, help="also write ANSI capture here")
    ap.add_argument("--lens-dir", default=DEFAULT_LENSES,
                    help="lens checkpoint dir (needs lens.pt + calibration.json)")
    args = ap.parse_args()

    d = torch.load(f"{args.lens_dir}/lens.pt", map_location="cpu", weights_only=True)
    cal = json.load(open(f"{args.lens_dir}/calibration.json"))["layers"]
    with safe_open(SNAP, framework="pt") as f:
        W_U = f.get_tensor("model.language_model.embed_tokens.weight").float()
        norm_w = f.get_tensor("model.language_model.norm.weight").float()
    tok = AutoTokenizer.from_pretrained(SNAP.rsplit("/", 1)[0])

    torch.manual_seed(1536)  # the width of the space we are lighting
    X = torch.randn(args.cols, d["d_model"])

    def decode_top1(Y: torch.Tensor) -> torch.Tensor:
        Yn = Y / Y.pow(2).mean(-1, keepdim=True).add(1e-6).sqrt() * (1.0 + norm_w)
        return (Yn @ W_U.T).argmax(-1)

    lines = []
    header = f"the same {args.cols} random directions, decoded through every layer's transport"
    lines.append(f"\x1b[2m{header}\x1b[0m")
    for layer in sorted(d["J"]):
        ids = decode_top1(X @ d["J"][layer].float().T).tolist()
        uniq = len(set(ids))
        c = cal[str(layer)]
        cells = []
        for i in ids:
            ch = (tok.decode([i]).strip() or "·")[0]
            if not ch.isprintable() or ord(ch) < 33:
                ch = "·"
            cells.append(f"\x1b[38;5;{hue_for(i)}m{ch}")
        flag = "◦" if c["low_rank"] else " "
        margin = f"\x1b[2m L{layer:>2}{flag} rank {c['eff_rank']:>6.1f} · {uniq:>3} voices\x1b[0m"
        lines.append("".join(cells) + RESET + margin)
    art = "\n".join(lines) + "\n"
    sys.stdout.write(art)
    if args.out:
        with open(args.out, "w") as f:
            f.write(art)
        print(f"[capture -> {args.out}]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
