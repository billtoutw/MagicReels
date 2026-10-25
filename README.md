# MagicReels

**把長文，做成有自己聲音的繁中短影音。**

MagicReels 是一套可重現、保留人工審核的製作工具包。從文章改寫提示詞開始，以 BreezyVoice 配音，編排素材與圖卡，輸出 1080 × 1920 影片及繁中字幕，再匯入配樂完成混音。

v0.2.0 · Python 3.11+ · FFmpeg / libass · 本機 CLI

[觀看完整示範（53 秒 MP4）](https://github.com/billtoutw/MagicReels/releases/download/v0.2.0/MagicReels-demo-v0.2.0.mp4) · [下載 v0.2.0](https://github.com/billtoutw/MagicReels/releases/tag/v0.2.0) · [查看示範輸入](examples/first-reel)

![MagicReels 示範畫面](examples/first-reel/preview.jpg)

## 先跑完整示範

安裝 Python 3.11+、Git 和含 `libass` 的 FFmpeg。以下指令從倉庫根目錄執行：

```sh
git clone https://github.com/billtoutw/MagicReels.git
cd MagicReels
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export PEXELS_API_KEY='your-key'
python examples/first-reel/fetch_materials.py
magicreels validate examples/first-reel/project.json
magicreels render examples/first-reel/project.json --out work/demo-film-v1
magicreels mix work/demo-film-v1/film.mp4 \
  --music examples/first-reel/music.wav --out work/demo-mix-v1
```

示範採 6 段 Pexels 動態影片與 2 張概念圖卡，保留已確認的旁白與配樂。觀看成品可直接開啟上方 MP4；重建請設定自己的免費 Pexels API key，執行下載腳本，再驗證與合成。配音已附於範例，無須另外下載語音模型。重跑時請換新的輸出目錄。

在 macOS 可用 `brew install ffmpeg`；Ubuntu 可用 `sudo apt-get install ffmpeg`。請以 `ffmpeg -filters` 確認有 `ass` 濾鏡。

## 製作自己的影片

| 步驟 | 操作與產出 | 人工確認 |
| --- | --- | --- |
| 1. 文章 → 腳本 | 將 [文章改寫提示詞](prompts/article-to-script.md) 與文章交給你使用的 LLM | 核對事實、正式名稱、主線與口白 |
| 2. 腳本 → 聲音 | 按 [BreezyVoice 安裝與操作](docs/breezyvoice.md) 生成分段音檔與 `audio-map.json` | 先聽短段，再聽完整音軌 |
| 3. 聲音 → 分鏡 | 複製示範的 `project.json`；依音訊段落安排圖卡、照片或影片 | 核對素材身分、來源與字幕斷行 |
| 4. 合成 | `magicreels validate`，再執行 `magicreels render` | 手機尺寸檢查與完整觀看 |
| 5. 音樂 → 完成 | 用 [配樂提示詞](prompts/music.md) 在 ElevenLabs 產生並下載音樂，執行 `magicreels mix` | 全片試聽人聲清晰度 |

輸入格式、局部修訂與指令見 [製作指南](docs/workflow.md)。Codex 或其他程式代理可以依此文件協作；步驟也可從一般終端機執行。文章改寫與 ElevenLabs 操作由使用者選擇的服務完成。

### 素材搜尋

```sh
# 在本機終端機設定自己的金鑰，勿寫入倉庫。
export PEXELS_API_KEY='your-key'
magicreels search 'person reading an article' --out work/search-v1
magicreels fetch 123456 --out work/asset-v1  # 將 123456 換成搜尋結果的 video_id
```

以 Pexels 動態影片優先，直式素材置中裁切為 1080×1920 滿版；缺少適合畫面或需要說明概念時再用圖卡。搜尋結果保存作者、來源頁與素材 ID，下載後附三張取樣圖。請觀看實際取段後設定 `reviewed: true`。

完整教學見 [Pexels 素材取得與使用](docs/pexels.md)，包括金鑰、搜尋、下載、分鏡及授權範圍。Pexels 素材依其授權使用，原始片段保存在 Git 忽略目錄；來源由 [Pexels](https://www.pexels.com) 提供。

### 配音與字幕

BreezyVoice 採獨立 Python 3.10 環境。參考聲音由使用者提供，正常稿與注音合成稿分開保存。每個短句的實際音檔邊界形成字幕時間表。需要字詞層級檢查時，可安裝 `python -m pip install -e '.[align]'` 並執行 `magicreels transcribe` 取得 Whisper 逐字時間；依試聽結果修正時間表。

### 固定版型

- 9:16、1080 × 1920、30 fps、H.264 / AAC。
- 思源黑體繁中粗體黃色字幕，最多兩行；思源宋體繁中粗體的白色引題與珊瑚紅問句。
- 右上角來源、暗色素材背景、動態影片滿版裁切，以及約 390 px 寬的檢查圖。
- 來源 ID 與檔案雜湊防止同一素材再次插入。變形或重新編碼的素材仍須靠來源 ID 與人工核對。
- 音樂以緩慢音量曲線調整，保存人聲成分與時間，混音前後比對解碼畫格。

## v0.2 範圍與現況

本版支援單支 1–180 秒影片、一套固定版型、本機 BreezyVoice、Pexels 搜尋、原創圖卡、照片／影片、逐段字幕與匯入配樂。CTA 可作為時間軸尾段，使用獨立素材。

服務帳號、雲端部署、批次發布、社群排程與線上編輯器留待需求驗證。影片事實、聲音聽感、素材身分與最終觀感由製作者確認。

測試範圍、硬體與已知限制見 [v0.2 驗證紀錄](docs/verification-v0.2.md)。BreezyVoice 的安裝較重，CPU 生成可能明顯慢於音檔長度；先完成短段試行再投入長片。

## 來源與授權

MagicReels 整理自實際的 Reelsturbo 製作流程。工作流起點為 [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo)，本倉庫抽出繁中編輯規格與獨立命令列工具，並明確保留各上游的來源。

本專案程式與原創文件採 [MIT](LICENSE)。BreezyVoice、字型、素材、音樂與服務條款各自適用，詳見 [第三方來源](THIRD_PARTY_NOTICES.md)。私人參考聲音、金鑰與既有客戶素材均由使用者保留在本機。

## 開發與回報

```sh
python -m unittest discover -s tests -v
```

回報問題時附操作指令、作業系統、FFmpeg 版本與可公開的最小範例。請先移除金鑰、個人聲音與未公開稿件。改善建議歡迎以 Issue 討論；維護方式見 [CONTRIBUTING.md](CONTRIBUTING.md)。
