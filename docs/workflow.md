# 製作指南

## 1. 準備一個專案

將 `examples/first-reel/` 複製到 `work/my-reel/`，保留目錄結構，替換文章、腳本、聲音與分鏡。所有 `project.json` 內的檔案路徑，以該 JSON 所在目錄為起點；音訊清單內路徑則以音訊清單所在目錄為起點。使用 UTF-8。

每支影片聚焦一個問題，先確認來源與口白。`script.txt` 每行一個短句；每句建議 10–20 個中文字，足以在兩行字幕內呈現。語意較長時可拆成連續句段；正式名稱保持原字，按語意分行。

## 2. 生成並確認聲音

按 [BreezyVoice 文件](breezyvoice.md) 先生成含人名、數字或問題詞的短段；中英夾雜依 [配音規則](breezyvoice-code-switching.md) 比對連讀、重音及前後語氣。短段確認後產生完整旁白。`audio-map.json` 保存每句的實際時間、正常稿與音檔雜湊。

聽完完整音檔後，由製作者執行：

```sh
magicreels approve-audio work/my-reel/voice/audio-map.json \
  --out work/my-reel/approval.json
```

這個指令只記錄人的決定。`audio-map.json` 保留生成當下的待試聽狀態，實際核准以獨立的 `approval.json` 為準。音檔一旦更動，先前核准即不適用。程式不會自動把辨識結果標記為人工核准。

需要檢查逐字時間時：

```sh
python -m pip install -e '.[align]'
magicreels transcribe work/my-reel/voice/narration.wav --out work/my-reel/asr-v1
```

首次會下載 Whisper small 模型。結果供試聽與時間校正使用；字幕沿用正常稿。目前預設每個 TTS 短句對應一筆字幕，以實際分段邊界對時。整段真人錄音可先依句分割，再使用 `magicreels.tts.assemble` 建立相同格式，或由編輯建立並核對時間表。

## 3. 編排畫面與字幕

`project.json` 的必要欄位：

| 欄位 | 用途 |
| --- | --- |
| `schema_version` | 固定為 `1` |
| `title` | 專案標題 |
| `audio_map` | 配音輸出的 `audio-map.json` 相對路徑 |
| `approval` | 完整旁白的人工核准紀錄 |
| `captions` | 依音訊段落排序的字幕；可用 `\n` 語意換行，最多兩行 |
| `hook` | `lead` 白色引題、`question` 珊瑚紅問句、`end_part` 最後一個 Hook 音訊段號 |
| `scenes` | 依序涵蓋全部旁白的分鏡 |

每筆分鏡都有 `source_asset_id`、`kind`、`parts` 與 `credit`。`parts` 從 1 起算，必須連續；例如 `[3,4]` 表示此素材在第 3 句開頭進場，持續到第 4 句結束。

圖卡：

```json
{
  "source_asset_id": "original:my-reel:card-02",
  "kind": "card",
  "parts": [3, 4],
  "title": "先選一個問題",
  "body": "觀眾最在意什麼？\n一句話寫出答案。",
  "credit": "概念示意／自行製圖"
}
```

動態影片優先；照片或影片格式：

```json
{
  "source_asset_id": "pexels:video:123456",
  "kind": "video",
  "parts": [5, 6],
  "path": "assets/clip-01/video.mp4",
  "source_in": 2.5,
  "source_page": "https://www.pexels.com/video/REPLACE-WITH-ACTUAL-SOURCE/",
  "reviewed": true,
  "title": "保留兩個重點",
  "credit": "示意畫面／Pexels"
}
```

以上 ID 與網址是格式占位，須換成實際來源。照片使用 `kind: "image"`，省略 `source_in`。動態影片置中裁切為滿版，優先選直式、主體居中的來源並核對裁切。照片保留完整比例置中。

圖解可使用 `kind: "diagram"`、`path` 與原創或生成素材來源，搭配 `body` 的兩行正常文字。圖解保留原始暗底亮度，正文由 ASS 精確排版。Pexels 詳細操作與使用條件見 [素材教學](pexels.md)。

素材只使用一次：相同原始素材即使改名、裁切或重新編碼，也保留相同 `source_asset_id`。同一素材可連續涵蓋多句；離場後再次出現會被拒絕。程式另外比較檔案雜湊，但變形素材的來源身分仍需製作者核對。

## 4. 驗證並合成

```sh
magicreels validate work/my-reel/project.json
magicreels render work/my-reel/project.json --out work/my-reel/film-v1
```

產出 `film.mp4`、`captions.srt`、`captions.ass`、`source-manifest.json`、`manifest.json`、`verification.json` 與 `preview.jpg`。

全片解碼、尺寸、影格率、影音尾差與來源唯一性由程式檢查。開啟 `preview.jpg` 檢查 390 px 寬版面，再完整觀看影片，特別檢查最長字幕、切點、片頭和片尾。

若文字超寬，程式會明確報錯。保留正式名稱，以語意換行處理；超過兩行的長句先回到腳本與配音分段調整。

## 5. 配樂與混音

依成片時長填入 [配樂提示詞](../prompts/music.md)，在 ElevenLabs 產生與下載檔案。需要的方案及使用權以當時服務條款為準。也可以匯入你已取得適用權利的音樂。

```sh
magicreels mix work/my-reel/film-v1/film.mp4 \
  --music work/my-reel/music.wav --out work/my-reel/mix-v1
```

配樂須至少涵蓋全片，程式不循環播放。混音採約 3 秒的音樂音量視窗與平滑增益，預設以人聲高於音樂約 18 dB 為起點，對較低的人聲視窗再降低配樂。這是 RMS 檢查，最終聽感請以耳機與手機喇叭確認。

輸出 `final.mp4`、字幕、`mix-settings.json`、技術驗證與檢查圖。人聲時間與增益保留，影片使用 stream copy，並以解碼畫格雜湊確認畫面一致。峰值過高時停止，讓製作者調整音量後重試。

## 局部修訂

每次指定新的輸出目錄。重錄受影響句段，保留已核准音檔，再以新音訊清單重建該版本。改變聲音長度後，分鏡仍按段號接回實際時間，字幕也使用新的邊界。素材與聲音的歷史核准紀錄留在原版本。
