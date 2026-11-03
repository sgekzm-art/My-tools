#!/usr/bin/env python3
"""「ふくのみせ」のセリフ音声を Gemini TTS で一括生成する。

使い方は README.md を参照。
既定では「まだ作っていない最初の1行」だけを生成する（料金確認のため）。
全行を作るときは --all を付ける。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
import time
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_MODEL = "gemini-3.8-flash-tts"
DEFAULT_RATE = 24000  # Gemini TTS は 24kHz / 16bit / モノラルの PCM を返す


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


def get_client():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        die(
            "環境変数 GEMINI_API_KEY が設定されていません。\n"
            "  1. https://aistudio.google.com/apikey で API キーを作成\n"
            "  2. ターミナルで設定:\n"
            "       macOS / Linux : export GEMINI_API_KEY=\"取得したキー\"\n"
            "       Windows (PowerShell): $env:GEMINI_API_KEY=\"取得したキー\"\n"
            "  3. もう一度このスクリプトを実行"
        )
    try:
        from google import genai
    except ImportError:
        die("google-genai が入っていません。 pip install google-genai を実行してください。")
    return genai.Client(api_key=key)


def load_lines(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    for need in ("cut", "speaker", "text"):
        if rows and need not in rows[0]:
            die(f"{path.name} に列 {need} がありません（必要な列: cut, speaker, text）")
    # 同じカット内の順番を付ける（例: 16-1, 16-2 ...）。CSV の並び順を保つ。
    seen: dict[int, int] = {}
    out = []
    for i, r in enumerate(rows, start=2):
        try:
            cut = int(r["cut"])
        except ValueError:
            die(f"{path.name} {i}行目: cut が数字ではありません: {r['cut']!r}")
        seen[cut] = seen.get(cut, 0) + 1
        out.append({"cut": cut, "n": seen[cut], "speaker": r["speaker"].strip(), "text": r["text"]})
    out.sort(key=lambda r: (r["cut"], r["n"]))
    return out


def out_name(row: dict) -> str:
    safe = re.sub(r'[\\/:*?"<>|\s]', "_", row["speaker"])
    return f"{row['cut']:02d}-{row['n']}_{safe}.wav"


def build_prompt(style: str, text: str) -> str:
    # 話し方は英語の DIRECTOR'S NOTES、読む文は TRANSCRIPT に分けて渡す。
    # 日本語で指示すると、指示文まで読み上げてしまうことがあるため。
    # セリフ本文は一切変えずに渡す。
    return (
        "### DIRECTOR'S NOTES\n"
        f"Style: {style}\n"
        "Language: Japanese. Speak ONLY the transcript below. "
        "Never read these notes aloud.\n\n"
        "### TRANSCRIPT\n"
        f"{text}"
    )


CHECK_MODEL = "gemini-3.5-flash"


def norm(t: str) -> str:
    return re.sub(r"[\s、。，．,.！？!?…「」『』（）()ー〜~・]", "", t)


def check_audio(client, path: Path, text: str) -> tuple[bool, str]:
    """音声を文字起こしして、セリフ以外（指示文など）を読んでいないか確かめる。"""
    from google.genai import types

    r = client.models.generate_content(
        model=CHECK_MODEL,
        contents=[
            types.Part.from_bytes(data=path.read_bytes(), mime_type="audio/wav"),
            "最後まで全部聞いて、話されている言葉をすべて一字一句文字起こししてください。"
            "文字起こし以外は書かないでください。",
        ],
    )
    heard = (r.text or "").strip()
    # 読み方の揺れ（漢字/かな）は許し、明らかに長いときだけ「余計なことを読んだ」とみなす
    ok = len(norm(heard)) <= len(norm(text)) * 1.4 + 4
    return ok, heard


def synth(client, model: str, voice: str, prompt: str) -> tuple[bytes, int]:
    from google.genai import types

    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                )
            ),
        ),
    )
    try:
        part = resp.candidates[0].content.parts[0]
        data = part.inline_data.data
        mime = part.inline_data.mime_type or ""
    except (AttributeError, IndexError, TypeError):
        raise RuntimeError(f"音声が返ってきませんでした: {resp}")
    if not data:
        raise RuntimeError("音声データが空でした")
    m = re.search(r"rate=(\d+)", mime)
    return data, int(m.group(1)) if m else DEFAULT_RATE


def save_wav(path: Path, pcm: bytes, rate: int) -> None:
    tmp = path.with_suffix(".part")
    with wave.open(str(tmp), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    tmp.replace(path)


def concat(files: list[Path], dest: Path) -> None:
    if not shutil.which("ffmpeg"):
        print("ffmpeg が見つからないため all.wav は作りませんでした（ffmpeg を入れると使えます）。")
        return
    if not files:
        print("繋ぐ音声ファイルがありません。")
        return
    listfile = dest.parent / "concat_list.txt"
    listfile.write_text(
        "".join(f"file '{p.name}'\n" for p in files), encoding="utf-8"
    )
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(listfile), "-ar", str(DEFAULT_RATE), "-ac", "1", str(dest)],
    )
    listfile.unlink(missing_ok=True)
    if r.returncode == 0:
        print(f"カット順に繋ぎました: {dest}")
    else:
        print("ffmpeg での結合に失敗しました。")


def list_voices(client) -> None:
    try:
        res = client.voices.list(type_=["prebuilt"], page_size=100)
        voices = getattr(res, "voices", None) or []
        for v in voices:
            print(f"{getattr(v, 'id', '')}\t{getattr(v, 'gender', '') or ''}\t"
                  f"{getattr(v, 'description', '') or ''}")
        if voices:
            return
    except Exception as e:  # 古い SDK や未対応地域では使えないことがある
        print(f"（声の一覧 API を使えませんでした: {e}）")
    print("公式ドキュメントの一覧を参照してください: "
          "https://ai.google.dev/gemini-api/docs/speech-generation")


def list_models(client) -> None:
    for m in client.models.list():
        if "tts" in (m.name or ""):
            print(m.name.removeprefix("models/"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Gemini TTS でセリフ音声を一括生成")
    ap.add_argument("--all", action="store_true", help="全行を生成（既定は未生成の最初の1行だけ）")
    ap.add_argument("--force", action="store_true", help="既にあるファイルも上書きして作り直す")
    ap.add_argument("--cut", type=int, action="append", help="このカット番号だけ生成（複数指定可）")
    ap.add_argument("--concat", action="store_true", help="生成後、ffmpeg でカット順に繋いで all.wav を作る")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"TTS モデル名（既定: {DEFAULT_MODEL}）")
    ap.add_argument("--lines", default=str(HERE / "lines.csv"))
    ap.add_argument("--voices", default=str(HERE / "voices.json"))
    ap.add_argument("--out", default=str(HERE / "out"))
    ap.add_argument("--check", action="store_true",
                    help=f"生成後に {CHECK_MODEL} で文字起こしし、指示文まで読んでいたら作り直す（最大2回）")
    ap.add_argument("--dry-run", action="store_true", help="API を呼ばず、作る予定のファイルと指示文を表示")
    ap.add_argument("--list-voices", action="store_true", help="使える声の一覧を表示して終了")
    ap.add_argument("--list-models", action="store_true", help="使える TTS モデルの一覧を表示して終了")
    args = ap.parse_args()

    if args.list_voices or args.list_models:
        client = get_client()
        if args.list_models:
            list_models(client)
        if args.list_voices:
            list_voices(client)
        return

    rows = load_lines(Path(args.lines))
    voices = json.loads(Path(args.voices).read_text(encoding="utf-8"))
    missing = sorted({r["speaker"] for r in rows} - voices.keys())
    if missing:
        die(f"voices.json に次の話者がありません: {', '.join(missing)}")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    targets = [r for r in rows if not args.cut or r["cut"] in args.cut]
    todo = [r for r in targets if args.force or not (out_dir / out_name(r)).exists()]
    skipped = len(targets) - len(todo)
    if not args.all and not args.cut:
        todo = todo[:1]

    if not todo:
        print(f"作る行はありません（既存 {skipped} 件はスキップ。作り直すなら --force）。")
    client = None if args.dry_run or not todo else get_client()

    failures: list[tuple[str, str]] = []
    made = 0
    for r in todo:
        v = voices[r["speaker"]]
        name = out_name(r)
        prompt = build_prompt(v.get("style_en") or v["style"], r["text"])
        print(f"[{r['cut']:02d}-{r['n']}] {r['speaker']}（{v['voice']}）: {r['text']}")
        if args.dry_run:
            print(f"    → {name}\n    指示文: {prompt!r}")
            continue
        redo = 0
        for attempt in range(3):
            try:
                pcm, rate = synth(client, args.model, v["voice"], prompt)
                save_wav(out_dir / name, pcm, rate)
                if args.check:
                    ok, heard = check_audio(client, out_dir / name, r["text"])
                    print(f"    聞こえた内容: {heard}")
                    if not ok:
                        (out_dir / name).unlink(missing_ok=True)
                        if redo < 2:
                            redo += 1
                            print("    セリフ以外も読んでいるようなので作り直します")
                            continue
                        raise RuntimeError(f"セリフ以外を読んでしまいました: {heard}")
                print(f"    → 保存しました: out/{name}")
                made += 1
                break
            except Exception as e:
                msg = str(e)
                retry = attempt < 2 and re.search(r"429|500|503|RESOURCE_EXHAUSTED|UNAVAILABLE", msg)
                if retry:
                    wait = 5 * (attempt + 1)
                    print(f"    一時的なエラー。{wait}秒後に再試行します: {msg[:120]}")
                    time.sleep(wait)
                    continue
                print(f"    × 失敗: {msg[:300]}")
                failures.append((name, msg))
                break

    print(f"\n生成 {made} 件 / スキップ（既存） {skipped} 件 / 失敗 {len(failures)} 件")
    if failures:
        print("失敗した行:")
        for name, msg in failures:
            print(f"  - {name}: {msg.splitlines()[0][:200]}")
    if not args.all and not args.cut and not args.dry_run and made:
        print("\n最初の1行だけ作りました。聴いて問題なければ、--all を付けて全行を生成してください。")

    if args.concat and not args.dry_run:
        files = [out_dir / out_name(r) for r in rows if (out_dir / out_name(r)).exists()]
        concat(files, out_dir / "all.wav")

    if failures:
        sys.exit(2)


if __name__ == "__main__":
    main()
