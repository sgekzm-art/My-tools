#!/usr/bin/env python3
"""通し音声（out/all.wav）に合わせて、カットごとの文字カードを並べた絵コンテ動画を作る。

先に `python3 make_voices.py --concat` を実行して out/all.wav と out/all_cuts.json を作っておく。
出力: out/animatic.mp4（縦 720x1280）
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
W, H = 720, 1280
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"

SCENE_COLORS = {
    "導入": "#2f3e5c", "迷い込んだ親子": "#3d4f6e", "ジョンが手こずる": "#7a5a2a",
    "ちゃこ姉ちゃんの問い": "#5b4a6e", "回想": "#555555", "答え": "#7a4a2a",
    "料理": "#8a4b2a", "男の子の食事": "#7a6a2a", "食べきる": "#8a3f3f",
    "ねぎらう": "#8a3f5a", "帰り道": "#3f5a7a", "ラスト": "#2f5a4a",
}


def load_script() -> list[dict]:
    rows = []
    for line in (HERE / "script_ep1.md").read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|([^|]*)\|([^|]*)\|([^|]*)\|([^|]*)\|", line)
        if m:
            scene = re.sub(r"\*\*|（新）", "", m.group(3)).strip()
            rows.append({"cut": int(m.group(1)), "scene": scene,
                         "who": m.group(4).strip(), "line": m.group(5).strip()})
    return rows


def wrap(text: str, width: int) -> list[str]:
    out = []
    for para in re.split(r"(?<=[」）])\s+|\s{2,}|　", text):
        out += textwrap.wrap(para, width) or [""]
    return out


def card(row: dict, path: Path) -> None:
    bg = SCENE_COLORS.get(row["scene"], "#333333")
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    big = ImageFont.truetype(FONT, 64)
    mid = ImageFont.truetype(FONT, 40)
    small = ImageFont.truetype(FONT, 34)
    d.text((48, 80), f"カット {row['cut']}", font=big, fill="white")
    d.text((48, 170), row["scene"], font=mid, fill="#ffe9b0")
    d.text((48, 230), row["who"], font=small, fill="#dddddd")
    y = 340
    text = row["line"] if row["line"] not in ("—", "") else "（BGMのみ）"
    for ln in wrap(text, 18):
        d.text((48, y), ln, font=small, fill="white")
        y += 52
        if y > H - 120:
            break
    d.text((48, H - 80), "ふくのみせ 第1話 絵コンテ", font=ImageFont.truetype(FONT, 26), fill="#bbbbbb")
    im.save(path)


def main() -> None:
    cuts_path = OUT / "all_cuts.json"
    if not cuts_path.exists():
        sys.exit("先に python3 make_voices.py --concat を実行してください。")
    info = json.loads(cuts_path.read_text(encoding="utf-8"))
    starts = {int(k): v for k, v in info["cut_starts"].items()}
    total = info["total"]
    script = {r["cut"]: r for r in load_script()}
    order = sorted(starts)
    frames = OUT / "animatic_frames"
    frames.mkdir(exist_ok=True)
    lines = []
    for i, c in enumerate(order):
        end = starts[order[i + 1]] if i + 1 < len(order) else total
        p = frames / f"{c:02d}.png"
        card(script.get(c, {"cut": c, "scene": "", "who": "", "line": ""}), p)
        lines.append(f"file '{p}'\nduration {end - starts[c]:.3f}\n")
    lines.append(f"file '{frames / f'{order[-1]:02d}.png'}'\n")
    lst = frames / "list.txt"
    lst.write_text("".join(lines), encoding="utf-8")
    dest = OUT / "animatic.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-i", str(OUT / "all.wav"), "-vf", "fps=10,format=yuv420p", "-c:v", "libx264",
                    "-c:a", "aac", "-b:a", "128k", "-shortest", str(dest)], check=True)
    print(f"絵コンテ動画を作りました: {dest}")


if __name__ == "__main__":
    main()
