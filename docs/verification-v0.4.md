# v0.4.0 驗證紀錄

日期：2026-10-28。

## 版本與範圍

主要配音入口改為 Qwen3-TTS 1.7B Base BF16，透過 MLX Audio 在 Apple Silicon Mac 本機搭配參考錄音與逐字稿複製聲線。新增 `magicreels-qwen`；Voicebox App 無須安裝。套件、CLI 及新影片 manifest 使用 `0.4.0`。

既有 BreezyVoice CLI、讀音規則與 v0.2 示範保持相容，歷史示範及核准紀錄保留原版本。渲染、素材唯一性、人聲優先混音與人工核准流程沿用既有契約。

## 自動測試

`python -m unittest discover -s tests -v`：24 項通過，包含：

- Qwen 同音字、數字及英文名稱邊界；拒絕空字串、斷句及控制字元。
- 固定增益、內部樣本比例、5 ms 邊界淡化、150 ms 尾端靜音及峰值保護。
- 24 kHz／24-bit PCM 合併的逐樣本保留、時間表與不相容格式拒絕。
- 不支援的平台在載入模型前停止；無效參考錄音保存失敗紀錄；已有目錄拒絕覆寫。
- 既有 BreezyVoice 字典、聲音核准雜湊、素材唯一性、版本一致性、字幕及實際 FFmpeg 合成測試。

內附示範 `fetch_materials.py --check-only` 與 `magicreels validate` 通過，旁白雜湊及來源紀錄符合原始版本；示範素材、核准檔、字型與歷史音檔未修改。

## 安裝包與 Mac 實際生成

使用 `uv build --wheel` 建置 `magicreels-0.4.0-py3-none-any.whl`，在全新的獨立 Python 3.11 環境，依 Qwen 版本約束安裝 wheel 與可選依賴。從倉庫外執行，確認載入的是安裝後套件、CLI 為 `0.4.0`、MLX Audio 為 `0.4.1`。

使用已存在的固定 revision 模型快取與本機授權參考聲音，設定 `HF_HUB_OFFLINE=1`，由安裝後的 `magicreels-qwen` 生成一段原創短句：

| 項目 | 結果 |
| --- | --- |
| 模型 | Qwen3-TTS 1.7B Base BF16 |
| MLX 模型 revision | `a6eb4f68e4b056f1215157bb696209bc82a6db48` |
| 硬體 | Apple Silicon Mac，24 GiB 記憶體 |
| 完整音檔 | 3.11 秒，24 kHz，24-bit，單聲道 |
| 生成與處理時間 | 約 35.4 秒，單次量測 |
| 輸出樣本峰值 | 約 0.7121 |
| 削波樣本 | 0 |
| WAV／MP3 全片解碼 | 通過 |
| 分段及合併 PCM 比對 | 完全一致 |
| 人工核准 | `pending`，未自動核准 |

發布包檢查包含新入口，未包含私人參考錄音、測試音檔、模型權重、金鑰或正式製作素材。公開流程採用此前試聽確認的模型及處理方法；本次安裝包短段用於執行與訊號完整性驗證。

## 尚未驗證

本次沿用已下載的模型快取，未重新下載完整模型。新安裝包的短段尚未由使用者試聽；新稿的讀音、聲線、口音、完整尾句與整體語氣仍須短段及全軌驗收。ASR 與數值檢查僅作輔助。

Linux、Windows、Intel Mac 及其他記憶體容量的 Qwen 生成未驗證；核心剪輯流程及既有示範沿用原有平台範圍。本次未重建整支公開示範影片或在新的 Codex／Claude Code 對話從零製片。GitHub Actions 的實際結果請以倉庫 Actions 為準。
