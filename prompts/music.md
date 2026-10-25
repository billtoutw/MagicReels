# 配樂提示詞

把以下內容依影片主題與實際片長調整，貼到 ElevenLabs 的音樂生成功能。先檢查目前方案與使用條款，再下載 WAV 或 MP3。將音樂放入自己專案的 `work/` 目錄。

```text
Create an original instrumental background score for a Traditional Chinese educational short video about turning a long article into a focused short story.

Duration: [actual video duration plus 3 seconds].
Mood: clear, curious, warm, measured.
Arrangement: soft plucked notes, restrained synth pads, light percussion, a simple recurring motif.
Energy: a gentle opening, a small lift in the middle, and a resolved ending.
Keep the midrange spacious for spoken narration. Avoid vocals, spoken words, dramatic impacts, dense melodies, and sudden volume jumps. Keep the score supportive throughout.
```

以實際音檔長度代入，按內容替換主題與情緒。`magicreels mix` 會依人聲調低配樂並產生檢查紀錄；完成後仍須從頭試聽。

公開示範的 `music.wav` 由 `examples/first-reel/make_music.py` 生成原創簡單電子配樂，用來讓下載倉庫的人直接重建全流程。它展示相同的音樂匯入與混音接點。ElevenLabs 產出的音樂不隨倉庫散布。
