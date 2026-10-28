# BreezyVoice 本機配音

本頁保留 v0.1–v0.3 與內附示範使用的歷史入口。v0.4 的主要配音流程請使用 [Qwen3-TTS／MLX Audio](qwen3-tts.md)；既有 BreezyVoice 指令及輸出格式保持相容。

MagicReels 的配音命令是 `python magicreels/tts.py`。它使用使用者提供的參考錄音，輸出正常稿、注音合成稿、替換紀錄、分段 WAV、完整 WAV／MP3，以及可攜的 `audio-map.json`。

## 已整理的環境

本版安裝腳本針對 macOS Apple Silicon，使用獨立 Python 3.10、CPU 推論與 4 個 Torch 執行緒。先安裝 Miniforge、uv、Git、FFmpeg，確認 `conda`、`uv`、`ffmpeg` 可執行，再從倉庫根目錄執行：

```sh
./breezy/setup.sh .runtime/breezy
```

安裝會下載數 GB 模型與依賴，請預留至少 10 GB 空間。每次指定新的 runtime 目錄；失敗的目錄保留供診斷。安裝腳本不會改動既有 Python 環境。

固定來源：

- [BreezyVoice 原始碼](https://github.com/mtkresearch/BreezyVoice)：`d592c9d3e8927a0f53f68616387060dcd32a05ea`。
- [官方模型](https://huggingface.co/MediaTek-Research/BreezyVoice)：`e33b502e0ac21c16b0ee0d00df66ac3fa737393d`。
- `breezy/requirements-lock.txt` 保存既有成功環境版本；`model-manifest.json` 保存模型大型檔案的官方 SHA-256。
- `macos-normalization.patch` 保留繁體中文供 G2PW 處理，並避免末尾注音處理誤刪中文字。修正另附 Apache-2.0 授權。

Linux 使用者可依官方環境安裝方式準備 `upstream/`、`models/BreezyVoice/` 與 G2PW，再把所在目錄傳給 `--runtime`。本版 Linux 的完整配音環境尚未驗證；請先做短段試行。

## 提供自己的聲音

準備 3–30 秒、單人、無配樂的完整錄音，以及逐字相符的 UTF-8 文字。建議 5–15 秒。將私人檔案放在 `work/` 或其他不公開位置；確認你有使用該聲音的同意。

```sh
.runtime/breezy/env/bin/python magicreels/tts.py \
  --text '這次測試，會比較聲音相似度。' \
  --runtime .runtime/breezy \
  --reference work/my-reel/reference.wav \
  --reference-text work/my-reel/reference.txt \
  --pronunciations work/my-reel/pronunciation.json \
  --out work/my-reel/preview-v1
```

沒有問題詞時可省略 `--pronunciations`。字典格式例如：

```json
{"聲音": "聲[:ㄕㄥ1]音"}
```

以詞為單位處理實際遇到的中文讀音問題，保留原字，只加入注音；字典採較長詞優先、單次替換。英文單字可使用拼讀別名，例如 `"Codex": "CodeX"`、`"Bill": "bill"`，依大小寫及完整名稱邊界處理。別名限英文字母，字幕與顯示稿保持原名。中英連讀、重音、停頓、整句重錄與前後語氣的完整規則見 [中英夾雜配音指南](breezyvoice-code-switching.md)，可按語境選用 [範例字典](../examples/pronunciation-code-switching.json)。

先試聽人名、數字、讀音與停頓。短段確認後，改用完整稿：

```sh
.runtime/breezy/env/bin/python magicreels/tts.py \
  --script work/my-reel/script.txt \
  --runtime .runtime/breezy \
  --reference work/my-reel/reference.wav \
  --reference-text work/my-reel/reference.txt \
  --pronunciations work/my-reel/pronunciation.json \
  --out work/my-reel/voice
```

`script.txt` 每行或每個句號／問號／驚嘆號為一段。單段最多 120 字；公開版兩行大字幕適合更短的句段。生成後整軌音量目標為 -16 LUFS、真峰值 -1.5 dBTP，並按原始樣本數切回各段，保留語速。

完整旁白試聽完成後，依 [製作指南](workflow.md) 保存核准紀錄，再合成影片。失敗時保存已完成音檔及錯誤類型，修正原因後以新目錄重試。

## 公開示範聲音

`examples/first-reel/voice/` 使用官方倉庫的 `data/example.wav` 作為參考。來源與逐字稿可由固定 commit 取得；本倉庫不附參考音檔。範例用於展示流程，請以自己的授權聲音製作正式內容。

CPU 速度取決於硬體、句長與模型載入；本版實測及尚未驗證的部分記在 [驗證紀錄](verification.md)。
