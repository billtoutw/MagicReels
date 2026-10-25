# 用 Pexels 取得並編排短影音素材

Pexels 提供現成照片與動態影片的搜尋、下載。本流程把這些素材與旁白、字幕、圖卡編成完整影片。MagicReels 以 **Pexels 動態影片優先、直式滿版呈現**，抽象概念再搭配圖卡。

## 使用範圍

Pexels License 允許免費下載、修改及許多商業／非商業用途；實際使用仍須符合授權條件。人物、商標、建築等第三方權利可能另需同意。素材的完整權利範圍以來源頁與 [Pexels 授權](https://www.pexels.com/license/) 為準。

現行 [服務條款](https://www.pexels.com/terms-of-service/) 對單獨散布素材、誤導性背書、不當描繪可辨識人物及政治情境等設有限制。政治議題片宜採另行取得明確授權的素材或原創圖解。明確標示 CC0 的素材依該標示判斷；免費下載不等於所有權利皆已放棄。

本專案提供程式與完整創作成品，原始 Pexels 影片由使用者自行下載至 Git 忽略目錄。原素材保留其原授權。授權查核日期：2026-10-25。

## 1. 取得金鑰與搜尋

在 [Pexels API](https://www.pexels.com/api/) 取得自己的 API key，於本機終端機設定：

```sh
export PEXELS_API_KEY='your-key'
magicreels search 'writing notebook desk' --out work/search-notebook-v1
```

指令優先搜尋直式影片，輸出 `candidates.json`，包含素材 ID、作者、來源頁、長度與尺寸。搜尋詞應描述具體的「主體＋動作＋場景」，例如 `podcast microphone recording`、`audio mixing studio`。搜尋結果仍須觀看核對。

## 2. 下載、查看畫格與完整取段

從候選清單選擇 `video_id`。例如以下示範使用 ID 8873342；可換成你實際選定的數字：

```sh
magicreels fetch 8873342 --out work/asset-8873342-v1
```

產出 `video.mp4`、`source.json` 與原片約 15%、50%、80% 的三張取樣圖。先看取樣，再觀看預計使用的完整段落。確認主體、動作、身分、鏡頭運動，以及直式裁切後的重點。

素材須足以涵蓋該段旁白，保留剪輯餘裕。片長不足時補找其他來源；同一原始素材在全片只連續使用一次。

## 3. 放進分鏡並滿版合成

在自己的專案目錄內放置下載資料夾，依 `source.json` 填入實際來源：

```json
{
  "source_asset_id": "pexels:video:8873342",
  "kind": "video",
  "parts": [1, 2],
  "path": "assets/8873342/video.mp4",
  "source_in": 0.5,
  "source_page": "從 source.json 複製實際來源網址",
  "reviewed": true,
  "title": "從長文開始",
  "credit": "示意畫面／Pexels"
}
```

`parts` 對應音訊清單的句段號；`source_in` 為原影片取段起點。來源網址須替換為實際頁面，完成觀看核對後再設定 `reviewed: true`。

```sh
magicreels validate work/my-reel/project.json
magicreels render work/my-reel/project.json --out work/my-reel/film-v1
```

影片放大至覆蓋 1080×1920，再置中裁切為滿版。優先選直式、主體位於中央的素材，減少裁掉人物與重要物件。黑色遮罩、紅色重點字與黃色大字幕由程式疊加。

## 4. 保存來源與製作紀錄

保留素材 ID、作者、原始頁、授權頁、檔案雜湊、取段起點與使用段落。依 [API 指引](https://www.pexels.com/api/documentation/) 提供 Pexels 連結並盡可能標示作者；MagicReels 的來源表會保存作者與原始頁。

示範動態素材由 [Pexels](https://www.pexels.com) 提供。完整示範的作者及來源見 `examples/first-reel/materials.json`。

## 重建 v0.2 示範

```sh
python examples/first-reel/fetch_materials.py
magicreels validate examples/first-reel/project.json
magicreels render examples/first-reel/project.json --out work/demo-film-v2
magicreels mix work/demo-film-v2/film.mp4 \
  --music examples/first-reel/music.wav --out work/demo-mix-v2
```

原始片段下載至 `examples/first-reel/assets/pexels/`，該目錄已列入 Git 忽略。示範來源可能異動或下架；下載內容與記錄不同時須重新核對來源與分鏡。
