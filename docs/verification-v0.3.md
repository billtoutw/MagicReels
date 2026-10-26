# v0.3.0 驗證紀錄

日期：2026-10-26。

## 本次變更

- README 開頭加入可貼給 ChatGPT Codex 或 Claude Code 的最簡使用指令，連到可攜的 `AGENTS.md`、製作指南與配音文件。
- 中英夾雜指南整理實際 v1–v9 的讀音、斷句、連貫及語氣微調，並標示進階語音單元／CFM 方法的範圍。
- 配音字典支援單一英文單字拼讀別名，保留大小寫與名稱邊界；中文繼續保留原字及注音驗證。
- CLI、套件與新輸出 manifest 使用 0.3.0；歷史示範及驗證紀錄保留原版本。

## 本機驗證

在 macOS Apple Silicon 的既有 Python 3.11 環境與 FFmpeg 執行：

```sh
python -m unittest discover -s tests -v
python examples/first-reel/fetch_materials.py --check-only
python -m magicreels.cli --version
```

- 17 項測試通過，包含原有實際合成、滿版影片、圖卡、來源唯一性、人聲成分與音樂餘裕檢查。
- 英文別名確認 `Bill`／`Codex` 可以緊鄰中文字替換，`Bill2`、`Bill_v2`、`BillGates`、`XCodex`、`CodexAPI` 及不同大小寫保持原樣。
- 拒絕中文字替換、含空白或標點的英文別名、數字名稱替換與 Fish 音素標記；保留既有注音與單次替換處理。
- 範例讀音字典可通過入口驗證，合成標記還原後與正常稿一致；字幕與顯示稿保持原名。
- `pyproject.toml`、CLI `--version`、套件 `__version__` 與合成 manifest 版本一致。
- 既有示範的來源紀錄與旁白雜湊檢查通過，原始示範資料與音檔保持原樣。

使用 `uv build --wheel` 完成 0.3.0 wheel 建置，再以 `uv pip install --target <獨立目錄> --no-deps <wheel>` 安裝；沿用既有依賴並從倉庫外驗證套件實際載入位置、CLI 版本與讀音別名，全部通過。本次 Markdown 相對連結與提交範圍已核對。GitHub Actions 使用相同測試命令及示範來源檢查；各次執行結果見倉庫 Actions。

## 驗證範圍

本版未重新下載完整 BreezyVoice 模型或生成新的正式配音；單元測試驗證字典轉換與程式契約，聲音自然度仍依每份新稿的短段與整軌試聽確認。語音單元抽換、CFM 整句重建及同文 RMS 匹配目前是方法紀錄，公開 CLI 尚未提供通用自動修補入口。

AI 起手式與文件中的命令、路徑已核對；未在新的 ChatGPT Codex／Claude Code 對話各自從零製作整支影片。Linux 的完整 BreezyVoice 配音環境與其他硬體效能仍依 [既有紀錄](verification.md) 的限制處理。

示範 MP4／字幕沿用 [v0.2.0](verification-v0.2.md)；這次沒有重新合成示範音軌或更換畫面。個人聲音參考、個人照片、私人目錄與金鑰均留在本機。
