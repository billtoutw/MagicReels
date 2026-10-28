# Changelog

## 0.4.0 — 2026-10-28

- Make Qwen3-TTS 1.7B Base BF16 through MLX Audio the primary Apple Silicon narration workflow, using a local reference recording and exact transcript for voice cloning.
- Add `magicreels-qwen`, pinned model/runtime versions, isolated setup instructions and a Qwen-specific synthesis dictionary. Voicebox App is not required.
- Preserve normal display copy, per-part audio maps, hash-bound listening approval, versioned outputs and failure artifacts. Keep Qwen's constant-gain 24 kHz / 24-bit PCM unchanged during assembly.
- Update the AI quickstart, agent instructions and workflow; retain the legacy BreezyVoice CLI and the original v0.2 demo and approvals.
- Add regression coverage for Qwen pronunciation boundaries, signal processing, exact PCM assembly, reference validation and platform checks.

## 0.3.0 — 2026-10-26

- Put a copyable ChatGPT Codex / Claude Code production prompt at the beginning of the README and add portable agent instructions.
- Document mixed Chinese/English narration: targeted Bopomofo, connected English names, semantic phrasing, whole-sentence revisions, style matching and listening acceptance.
- Add an optional pronunciation dictionary and English single-word aliases with case-sensitive name boundaries; keep Chinese original-character validation and normal subtitle copy.
- Preserve the local-first BreezyVoice path and fixed approved voice/style references; record advanced CFM/unit repair as research methods with explicit limits.
- Add regression coverage for aliases, the example dictionary and package/CLI/render version consistency.
- Keep the existing v0.2 demo assets and approvals unchanged.

## 0.2.0 — 2026-10-25

- Replace the text-card demo with six unique Pexels motion shots and two supporting concept diagrams.
- Fill the vertical canvas with video footage and retain exact native Traditional Chinese typography.
- Preserve the approved narration and music, with an encoded-audio hash check on the visual revision.
- Add Pexels search/download/import and license guidance, source manifests and a reproducible material download script.
- Use current Pexels `/v1/videos/` endpoints and prefer portrait candidates.

## 0.1.0 — 2026-10-25

- Initial Traditional Chinese article-to-reel toolkit.
- Portable BreezyVoice narration entry and Apple Silicon setup instructions.
- Pexels candidate search and source records.
- Fixed 9:16 editorial template, original cards, image/video shots and SRT/ASS subtitles.
- Audio approval tied to the actual file hash; continuous timeline and source uniqueness checks.
- Voice-first music mixing with decoded-frame preservation checks.
- Original complete example with article, script, plan, narration, music and rendered release assets.
