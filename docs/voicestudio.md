# VoiceStudio 本機配音

MagicReels 使用 VoiceStudio v0.5.8 的本機 MLX Audio 後端，搭配 Qwen3-TTS 1.7B Base BF16 和使用者提供的參考聲音及逐字稿。這條路徑在 Apple Silicon Mac 上執行，使用獨立 Python 3.11 環境。MagicReels 負責分段計畫、合成稿、WAV／MP3 組裝與音訊映射。

## 安裝

準備 Git、uv 和 FFmpeg，從 MagicReels 根目錄執行：

```sh
git clone --depth 1 --branch v0.5.8 https://github.com/debpalash/VoiceStudio.git .runtime/voicestudio-v058/source
uv venv --python 3.11 .runtime/voicestudio-v058/venv
uv pip install --python .runtime/voicestudio-v058/venv/bin/python -e '.[voicestudio]'
```

已試行的 VoiceStudio 來源為 commit `c1050c16d9b3881e5d4161ee58ccc0582b3f20f9`，配音套件為 MLX Audio 0.5.0。Qwen3-TTS 模型沿用 [固定的 MLX 版本](qwen3-tts.md#安裝)，首次使用可能需要下載模型。參考音檔、逐字稿、工作檔與輸出請放在 Git 忽略的 `work/`，使用自己或已取得同意的聲音。

## 生成

在 MagicReels 根目錄設定本機後端路徑：

```sh
export PYTHONPATH="$PWD/.runtime/voicestudio-v058/source/backend:$PWD/.runtime/voicestudio-v058/source"
export OMNIVOICE_DATA_DIR="$PWD/.runtime/voicestudio-v058/data"
.runtime/voicestudio-v058/venv/bin/magicreels-voicestudio \
  --script work/my-reel/script.txt \
  --segments work/my-reel/segments.json \
  --reference work/my-reel/reference.wav \
  --reference-text work/my-reel/reference.txt \
  --out work/my-reel/voice-v1
```

`--script` 搭配完整語意段落的 `--segments`。可先加 `--plan-only` 並指定計畫輸出目錄，核對 `generation-plan.json`，再使用新的目錄正式生成。單次短段試聽可用 `--text` 傳入完整語意段。使用 [合成稿讀音字典](qwen3-tts.md#讀音修訂與正常稿分離)記錄數字讀法、局部字形轉換和已確認的多音詞，正常稿與字幕保留正字。

輸出包含原稿、合成稿、替換紀錄、分段 WAV、整軌 WAV／MP3 和 `audio-map.json`。核對檔案後先試聽短段與完整旁白，再按 [製作指南](workflow.md)進行對時和影片合成。局部重錄只替換受影響的語意段，保留其餘已核准的 PCM。需要重現舊流程時可獨立使用 [`magicreels-qwen`](qwen3-tts.md)。
