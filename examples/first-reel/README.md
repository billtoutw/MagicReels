# 第一支短片：長文如何變成短影音

這份範例包含完整的文章、正常口白稿、讀音字典、分鏡、生成音檔與配樂。

- `article.md`：原創教學文章。
- `script.txt`：15 個口白句段。
- `pronunciation.json`：本範例的 BreezyVoice 詞級讀音設定。
- `project.json`：6 個 Pexels 動態鏡頭與 2 張概念圖卡，每個來源只連續出現一次。
- `materials.json`：動態素材的 ID、作者、來源、檔案雜湊與取段。
- `fetch_materials.py`：用自己的 Pexels 金鑰下載原始影片。
- `assets/diagram-03.png`、`assets/diagram-08.png`：兩張 AI 輔助圖解；提示詞見 `visual-prompts.json`。
- `voice/`：公開示範旁白與可攜時間表，使用 BreezyVoice 官方範例聲線。
- `approval.json`：本次完整旁白試聽確認的音檔雜湊。
- `music.wav`：70 秒的原創電子配樂，涵蓋全片所需長度。
- `make_music.py`：配樂生成原始碼；重建前請先將既有 `music.wav` 移至其他位置，程式會拒絕覆寫。

從倉庫根目錄依 README 設定 Pexels 金鑰、下載動態素材，再驗證、合成與混音。輸出到 `work/`，既有範例保持原樣。

音樂可替換成使用者取得適用權利的 ElevenLabs 輸出；圖卡可以替換成已核對的照片或影片。素材搜尋與下載的指令見主 README。

範例的公開聲線僅用於示範。製作個人內容時，請提供自己的授權參考聲音。每次更動音檔，都應重新試聽並保存對應核准紀錄。

動態素材保存在 Git 忽略目錄；本倉庫提供來源表與下載腳本，成品 MP4 已完成剪輯、字幕與音樂組合。Pexels 片段的適用用途仍依 [素材授權教學](../../docs/pexels.md) 確認。
