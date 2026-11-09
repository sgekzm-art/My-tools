# My-tools

## スタンプ工房（line-stamp/）

ブラウザだけでLINEスタンプを作れるツールです。`line-stamp/index.html` をブラウザで開いて使います。

- 文字（8種類の書体・フチ文字）、ふきだしなどの図形、写真やイラスト（背景の自動透過つき）を組み合わせて作成
- スタンプ全体に白フチをつける
- 8 / 16 / 24 / 32 / 40 個から選択、提出前チェック（余白10px・空の枠）
- 「ZIPで保存」で `01.png`〜, `main.png`(240×240), `tab.png`(96×74) を一括書き出し
- 書き出したZIPは LINE Creators Market の「ZIPアップロード」で登録できます
- 作業内容はブラウザに自動保存されます

## 売れ筋分析
- `line-stamp-analysis/` … 人気LINEスタンプの傾向と、次に作るスタンプの企画（2026年11月）

## ふくちゃんの本音・あるある（fuku-honne-40/）
- 40個＋main/tab＋提出用ZIP（fuku-honne-40-line-stamps.zip）。写真はGemini、`src/build.py` で文字入れ（文字はChatGPTの手書き文字を切り出し。15・38・40 は Yusei Magic）

## 福 LINEスタンプ
- `fuku-stamps/` … 写真版（16個＋main/tab、提出用ZIP）
- `fuku-illust/` … イラスト版（16個＋main/tab、提出用ZIP）
  - `src/fuku.html` がキャラクターの描画元。`node src/render.js <フォント.ttf> <出力先>` → `python3 src/finish.py <出力先> fuku-illust` で再生成できます（フォント：Mochiy Pop One）
