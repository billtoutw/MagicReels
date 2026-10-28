# Qwen3-TTS 本機聲線複製

v0.4 使用 **Qwen3-TTS 1.7B Base（BF16）**，透過 **MLX Audio** 在 **Apple Silicon Mac 本機**生成音檔，搭配使用者的參考錄音與相符逐字稿複製聲線。入口是 `magicreels-qwen`，也可使用 `python -m magicreels.qwen`。此流程直接呼叫 MLX Audio，無須安裝 Voicebox App。

## 安裝

先安裝 Git、Python 3.11、FFmpeg 與 uv，從倉庫根目錄執行：

```sh
uv venv --python 3.11 .runtime/qwen
uv pip install --python .runtime/qwen/bin/python \
  -c qwen/requirements-lock.txt -e '.[qwen]'
```

配音依賴留在獨立環境，影片剪輯仍可沿用根目錄的 `.venv`。模型首次使用會從 Hugging Face 下載至本機快取，請預留數 GB 儲存空間；之後沿用快取。正式生成在本機進行，參考錄音與逐字稿留在本機輸出目錄。

固定版本：

- [Qwen3-TTS 1.7B Base BF16 的 MLX 模型](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16)，revision `a6eb4f68e4b056f1215157bb696209bc82a6db48`。
- [MLX Audio](https://github.com/Blaizzy/mlx-audio) `0.4.1`、MLX `0.32.4`，完整參考環境見 [依賴版本](../qwen/requirements-lock.txt)。
- 使用 Base 模型的參考聲音 encoder 與逐字稿；聲音自然度、口音與語氣以實際試聽確認。

本流程已於 Apple Silicon、24 GiB 記憶體環境使用。其他記憶體容量的效能尚未驗證；`magicreels-qwen` 會在不支援的平台停止。

Linux、Windows 與 Intel Mac 可參考 [README 的 Voicebox 平台及安裝說明](../README.md#voicebox)，另行生成旁白後依 [外部音訊銜接](workflow.md#voicebox-handoff)接回 MagicReels。這個可選流程仍需整理音訊映射與人工核准；目前的自動配音命令維持使用 MLX。

## 先生成短段

準備 3–30 秒、單人、無配樂的乾淨參考錄音，保留完整語句；逐字稿須與錄音相符。參考語氣應接近預期旁白。私人檔案放在 Git 忽略的 `work/`，使用自己或已取得同意的聲音。

```sh
.runtime/qwen/bin/magicreels-qwen \
  --text '這次測試，會比較聲音相似度。' \
  --reference work/my-reel/reference.wav \
  --reference-text work/my-reel/reference.txt \
  --out work/my-reel/preview-v1
```

若已有完整的本機模型資料夾，可加入 `--model /path/to/Qwen3-TTS-12Hz-1.7B-Base-bf16`，直接使用該資料夾。請核對來源與 revision；自訂路徑的紀錄保存 config 雜湊，`model_revision` 留空以免誤標。缺少 tokenizer encoder 會停止，不會改用其他聲音引擎。

先聽人名、英文名稱、數字、聲調、停頓與前後語氣。短段通過後，使用正常定稿：

```sh
.runtime/qwen/bin/magicreels-qwen \
  --script work/my-reel/script.txt \
  --reference work/my-reel/reference.wav \
  --reference-text work/my-reel/reference.txt \
  --out work/my-reel/voice-v1
```

每行或句號／問號／驚嘆號為一段，最多 120 字；優先保留完整語意句。影片目前每段對應一筆兩行字幕，較長句段需再依實際音檔對時、分割字幕。每次使用新的輸出目錄，保留已核准音檔。

## 讀音修訂與正常稿分離

建立這份稿件專用的 `work/my-reel/pronunciation.json`，再加上 `--pronunciations work/my-reel/pronunciation.json`。預設字典為空；以下只示範本次已試聽語境的寫法，新稿仍需逐句確認：

```json
{
  "2 兆": "兩兆",
  "預期": "育奇",
  "同期": "同旗"
}
```

同音字、數字讀法與英文別名只套用到 `synthesis-input.txt`，`display-script.txt` 及字幕保留正常文字。使用較長詞優先、單次替換；英文按大小寫與完整名稱邊界匹配。請用包含上下文的字詞縮小修訂範圍，避免把特定位置的修正套到其他段落。字典會拒絕空字串、斷句及控制字元。BreezyVoice 的注音格式另有專用入口。

英文名稱的個人讀法需在完整語句試聽；特定聲母或母音的效果無法只靠文字保證。修訂時先重生受影響的完整語意句，比較前後節奏，再接回其他核准片段。重組可使用 `magicreels.tts.assemble(..., preserve_pcm=True)`，輸入須為相同格式的單聲道 PCM WAV；重新保存核准紀錄與實際時間碼。

## 音檔與驗收

輸出包含正常稿、合成稿、替換紀錄、參考音檔及逐字稿、原始 FLOAT WAV、各段 24 kHz／24-bit WAV、完整 WAV／MP3 與 `audio-map.json`。

- 每段以固定 seed `42`、中文語言設定與最多 `640` 個音訊 token 生成；上游亦會依文字長度限制生成，尾句完整度須試聽確認。
- 使用固定增益，以 -23.1 LUFS 為目標、-1.5 dBFS 為樣本峰值上限；實際響度可能因峰值限制而較低。首尾各 5 ms 淡化，尾端加入 150 ms 靜音，語速保持原樣。
- 合併時保留完成處理的各段 PCM，音訊清單記錄實際樣本數、邊界、模型、參考雜湊及增益。MP3 為有損試聽副本。
- 完整解碼與數值檢查可驗證檔案完整性；口音、讀音、聲線與多餘語音仍需人工聽整軌。核准狀態先保留 `pending`。

完整旁白通過後，執行原有核准步驟：

```sh
magicreels approve-audio work/my-reel/voice-v1/audio-map.json \
  --out work/my-reel/approval-v1.json
```

接著按 [製作指南](workflow.md) 編排素材、字幕及影片。失敗時保存已完成片段及 `failure.json`，使用新目錄重試。v0.2 內附示範仍使用原始 BreezyVoice 音檔與既有核准紀錄；Qwen 的聲線與本機試行驗證見 [v0.4 紀錄](verification-v0.4.md)。
