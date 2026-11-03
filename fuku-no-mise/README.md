# ふくのみせ 音声生成（Gemini TTS）

第1話のセリフを、キャラごとの声で1行ずつ WAV に書き出します。

## ファイル
- `lines.csv` … セリフ一覧（列: `cut, speaker, text`）。男の子の声は入れていません。
- `voices.json` … 話者ごとの声（Gemini のプリセット音声名）と話し方の指示文
- `make_voices.py` … 生成スクリプト
- `out/` … 生成された音声（`01-1_ナレーション.wav`, `06-2_福.wav` …の順に並びます）

## 準備（初回だけ）
```bash
pip install google-genai
export GEMINI_API_KEY="AI Studio で作ったキー"   # Windows: $env:GEMINI_API_KEY="..."
```
キーは https://aistudio.google.com/apikey で作れます。キーはファイルに書かないでください。

## 使い方
```bash
python3 make_voices.py --dry-run --all   # API を呼ばずに、作るファイルと指示文を確認
python3 make_voices.py                   # まだ作っていない最初の1行だけ生成（料金確認用）
python3 make_voices.py --all             # 全行を生成（既にあるファイルは飛ばす）
python3 make_voices.py --all --concat    # 全行生成のあと ffmpeg でカット順に繋いで out/all.wav を作る
python3 make_voices.py --cut 6 --force   # カット6だけ作り直す
python3 make_voices.py --all --check     # 生成後に文字起こしで確認し、指示文まで読んでいたら作り直す
python3 make_voices.py --list-voices     # 使える声の一覧
python3 make_voices.py --list-models     # 使える TTS モデルの一覧
```
- 既定のモデルは `gemini-3.8-flash-tts`。`--model gemini-3.8-flash-lite-tts` で安い方に切り替えられます。
- 無料枠は「1モデルにつき1日10回」まで（2026年11月時点）。超えると 429 エラーになり、翌日（太平洋時間の0時）に戻ります。`--check` の確認は別モデルの枠を使います。
- 話し方の指示は `voices.json` の `style_en`（英語）を使います。日本語の指示だと、指示文まで読み上げてしまうことがあったためです。
- 失敗した行はエラーを表示して先に進み、最後にまとめて表示します。
- 声を変えたいときは `voices.json` の `voice` を書き換えて、`--cut <番号> --force` で作り直します。

## 声の初期設定（聴いて合わなければ変えてください）
| 話者 | 声 | 公式の特徴 |
| --- | --- | --- |
| 福 | Leda | Youthful（若々しい） |
| ジョン | Puck | Upbeat（元気） |
| ちゃこ姉ちゃん | Sulafat | Warm（温かい） |
| ママ | Achernar | Soft（やわらかい） |
| ナレーション | Despina | Smooth（なめらか） |
| 20代 | Callirrhoe | Easy-going（気楽） |
| 50代 | Gacrux | Mature（落ち着いた大人） |

他の候補の例: 福→Autonoe（Bright）、ジョン→Fenrir（Excitable）、ちゃこ→Vindemiatrix（Gentle）、ナレーション→Aoede（Breezy）。
