# YuE2 Instrumental ABC for ComfyUI

[English](README.md) | 日本語

YuE2が生成したABC楽譜を、インストゥルメンタル向けに編集するComfyUIカスタムノードです。

**Vocalの旋律を空いているIns小節へ移し、コード進行と既存のIns旋律を残したままVocalを休符化**できます。Vocalの休符化だけを行うノードも用意しています。

ABC文字列を処理するため、本ノード用のモデルや追加Pythonパッケージは不要です。音声生成には、別途YuE2を実行できるComfyUI環境が必要です。

## ノード一覧

カテゴリ: `YuE2/ABC`

| ノード | 処理 | 用途 |
| --- | --- | --- |
| **YuE2 Instrumentalize ABC** | 全休符のIns小節へVocal旋律をコピーし、Vocalを休符化 | 主旋律を残してインスト化したい場合 |
| **YuE2 Mute Vocal ABC** | Vocal音符だけを同じ長さの休符に変換 | Vocal旋律を取り除きたい場合 |

## インストール

### Gitでインストール

ComfyUIの `custom_nodes` ディレクトリで実行します。

```bash
git clone https://github.com/nappaniconico/yue2_instrumental_node.git yue2_instrumental
```

ComfyUIを再起動すると、ノード検索から追加できます。

### ZIPでインストール

1. このリポジトリの **Code → Download ZIP** からダウンロードします。
2. 展開したフォルダーを `yue2_instrumental` に変更し、ComfyUIの `custom_nodes` 内に配置します。
3. ComfyUIを再起動します。

次の構成になっていることを確認してください。

```text
ComfyUI/
└── custom_nodes/
    └── yue2_instrumental/
        ├── __init__.py
        ├── nodes.py
        ├── abc_mute.py
        └── instrumentalize.py
```

## 使い方

ABC生成と音声生成の間に、いずれかのノードを接続します。

```text
YuE2のABC生成ノード
        │ ABC文字列
        ▼
YuE2 Instrumentalize ABC
        │ abc出力
        ▼
YuE2の音声生成ノード
```

1. **YuE2 Instrumentalize ABC** を追加します。
2. 生成したABC文字列を `abc` 入力に接続します。ABCを直接貼り付けることもできます。
3. 本ノードの `abc` 出力を、音声生成ノードのABC入力に接続します。
4. `moved_bars` や `report` を表示用ノードなどに接続すると、処理結果を確認できます。

**Instrumentalizeには元のABCを入力してください。** Mute Vocalの後ろに接続すると、移植するVocal旋律がすでに消えています。

Vocal旋律を取り除く場合は、同じ位置に **YuE2 Mute Vocal ABC** を使用します。各YuE2ノードの表示名や入力名は、使用する拡張機能によって異なります。本ノードのABC入出力型は `STRING` です。

## YuE2 Instrumentalize ABC

### 処理内容

小節ごとに、以下のルールで変換します。

1. **Insが全休符でVocalに音符がある:** Vocal旋律をInsへコピーします。
2. **Insに音符がある:** その小節のIns全体を保持します。小節内の一部の休符への挿入は行いません。
3. **すべてのVocal音符:** 元の音価の休符へ変換します。コード記号はVocalの元の位置に残します。

`Z`、`Z2`、`Z3` などの複数小節休符と、`z4z4` など休符だけの通常小節に対応します。複数小節休符は必要な場合だけ展開します。

### 変換例

入力:

```abc
M:4/4
L:1/8
K:C
V: Vocal
"C"C4E4|"G"G8|
V: Ins
Z|d8|
```

出力:

```abc
M:4/4
L:1/8
K:C
V: Vocal
"C"z4z4|"G"z8|
V: Ins
=C4=E4|d8|
```

1小節目はVocal旋律をInsへ移し、2小節目は既存の `d8` を保持します。コード記号 `"C"` と `"G"` の位置は変わりません。

コピーする音符には臨時記号（自然音の `=` を含む）を明示し、元の調・臨時記号・小節をまたぐタイから決まる音程を保持します。移植した音符同士のタイは保持し、移植しない小節へ延びるタイは除去します。

### 入出力

入力は `abc`（`STRING`、元のABC）です。

| 出力 | 型 | 内容 |
| --- | --- | --- |
| `abc` | `STRING` | 変換後のABC |
| `muted_notes` | `INT` | Vocalで休符化した音符トークン数 |
| `moved_bars` | `INT` | Vocal旋律をInsへコピーした小節数 |
| `report` | `STRING` | 移植小節数・既存Insを優先した小節数などの要約 |

### 対応範囲

YuE2の単旋律ABCを対象とし、入力・変換後の両方を検証します。

- **必須:** `M:`（拍子）、`L:`（単位音価）、`K:`（調）が明記された単一曲。voice IDは `Vocal` と `Ins`。
- **小節:** 両voiceの小節数・各小節の長さ・単位音価・調・インライン転調位置が一致すること。小節末の小節線が必要です。
- **対応:** 長調・短調、通常音符・休符、分数音価、タイ、複数小節休符、`[K:...]` 転調、改行をまたぐ小節。
- **対象外:** 弱起などの不完全小節、連符、装飾、同時発音、反復記号、インラインvoice切替、歌詞 `w:`、Ins内のコード注釈など。

対応外の構文や長さの不一致はエラーで知らせます。自動でMute Vocal処理へ切り替えることはありません。元のコメント・ヘッダーを保持しますが、移植箇所の音符表記や空白位置は元と異なる場合があります。

## YuE2 Mute Vocal ABC

Vocalの音符を同じ長さの休符に変換し、不要になったタイを除去します。Insとその他のvoiceの音符は保持します。

入力:

```abc
V: Vocal
"C"C4E4|"G"G8|
V: Ins
Z|d8|
```

出力:

```abc
V: Vocal
"C"z4z4|"G"z8|
V: Ins
Z|d8|
```

入力は `abc`（`STRING`、元のABC）です。

| 出力 | 型 | 内容 |
| --- | --- | --- |
| `abc` | `STRING` | 変換後のABC |
| `muted_notes` | `INT` | Vocalで休符化した音符トークン数 |

音価、コード記号の位置、小節線、ヘッダー、コメント、改行を保持します。臨時記号、オクターブ、分数音価、インラインのvoice/key指定に対応します。Vocalの装飾音 `{...}` や同時発音 `[CEG]` はエラーにします。

このノードは汎用ABCバリデーターではありません。Mute Vocalで処理できるABCでも、Instrumentalizeの厳密な小節検証では対象外になる場合があります。

## よくある質問

### ノードが検索に表示されない

配置先が `custom_nodes/yue2_instrumental/__init__.py` になっているか確認し、ComfyUIを再起動してください。表示されない場合は、起動ログの読み込みエラーを確認してください。

### `muted_notes` が0になる

対象の音符がない場合は0になります。voice IDが大文字・小文字も含めて `Vocal` になっているか、すでに休符化したABCを入力していないか確認してください。タイでつながれた音符はトークンごとに数えます。

### `moved_bars` が0になる

Vocalに音符があり、対応するIns小節が全休符、という条件を満たす小節がない場合は0になります。Insに音符がある小節は移植対象になりません。

### 音声に歌声が残る／想定した楽器にならない

本ノードはABCを編集します。生成音声からのボーカル除去や楽器指定を行うものではありません。音声生成側の歌詞・スタイルもインスト用途に合わせてください。Mute Vocalは歌詞フィールドを変更せず、Instrumentalizeは歌詞 `w:` フィールドを受け付けません。外部の歌詞入力はどちらのノードも変更しません。

ABCの休符化・旋律移植だけで、歌声が出ないことや特定の楽器になることは保証できません。同じABC・シードで変換前後を比較すると、効果を確認しやすくなります。

## 開発・テスト

リポジトリのルートで実行します。

```bash
python -m unittest discover -s tests -v
```

テストはPython標準ライブラリだけで実行でき、ComfyUIやGPUは不要です。ノード登録、休符化、複数小節休符、既存Insの保持、音符の開始位置・音価・音程、コード位置、タイ、転調、対応外入力の検出を検証します。

## 参考

- [YuEリポジトリ](https://github.com/multimodal-art-projection/YuE)
- [YuE2公式ABC編集ガイド](https://github.com/multimodal-art-projection/YuE/blob/main/skills/yue2-music/references/abc-editing.md)
