# Third-party sources and asset provenance

MagicReels code and original documentation are MIT licensed. The components below retain their own terms. A code license does not automatically grant rights to a person's voice, a stock asset, or a hosted service's generated output.

| Component | Source | License / handling |
| --- | --- | --- |
| Workflow origin | [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | MIT. The original Reelsturbo workspace built on this project. MagicReels extracts the editorial workflow and standalone production scripts; it does not redistribute that workspace or its history. |
| Primary voice model | [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), [MLX BF16 conversion](https://huggingface.co/mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16) | Apache-2.0. Weights downloaded separately; the fixed revision is in `docs/qwen3-tts.md`. User reference audio stays local. |
| Apple Silicon voice runtime | [MLX Audio](https://github.com/Blaizzy/mlx-audio), [MLX](https://github.com/ml-explore/mlx) | MIT. Optional dependencies installed separately. Voicebox App is not required or bundled. |
| Voice measurements and WAV I/O | [pyloudnorm](https://github.com/csteinmetz1/pyloudnorm), [SoundFile](https://github.com/bastibe/python-soundfile) | MIT and BSD-3-Clause respectively; installed through the optional Qwen dependencies. SoundFile's libsndfile dependency retains its own LGPL terms. |
| Legacy voice inference and weights | [BreezyVoice](https://github.com/mtkresearch/BreezyVoice), [model card](https://huggingface.co/MediaTek-Research/BreezyVoice) | Upstream declares Apache-2.0. Downloaded separately. Pinned source/model revisions are in `docs/breezyvoice.md`. |
| macOS normalizer patch | `breezy/macos-normalization.patch`, derived from BreezyVoice `single_inference.py` | Modified to preserve Traditional Chinese and annotation boundaries. Apache-2.0 text is bundled at `breezy/Apache-2.0.txt`. |
| Demo narration | Generated with BreezyVoice using upstream `data/example.wav` at the pinned commit | Official reference used solely for the openly described demo. The reference recording itself is not bundled. No private personal voice was used. Generated output is not an endorsement by MediaTek Research or the reference speaker. |
| Sans font | [Source Han Sans](https://github.com/adobe-fonts/source-han-sans), unmodified `SourceHanSansTW-Bold.otf` | SIL OFL 1.1, bundled with `fonts/OFL-Sans.txt`. |
| Serif font | [Source Han Serif](https://github.com/adobe-fonts/source-han-serif), unmodified `SourceHanSerifTC-Bold.otf` | SIL OFL 1.1, bundled with `fonts/OFL-Serif.txt`. |
| Demo article, plan and graphic layout | Original MagicReels example | MIT for the original text and native layout. |
| Two concept illustrations | Built-in ImageGen; exact prompts in `examples/first-reel/visual-prompts.json` | AI-generated illustrative assets, distinct from Pexels footage. Check applicable output terms and third-party rights for reuse. |
| Demo music | Original score from `examples/first-reel/make_music.py` | MIT. Generated entirely from mathematical oscillators; no sampled recordings or third-party music. |
| Optional stock footage | [Pexels](https://www.pexels.com/license/) | Retrieved by users. Original stock clips are downloaded locally into a gitignored directory. The composed demo includes six Pexels shots; IDs, creators and source pages are recorded in `examples/first-reel/materials.json`. Review the current license and terms, including restrictions on political contexts and standalone distribution. |
| Optional music service | [ElevenLabs](https://elevenlabs.io/terms-of-use) | Separate service terms and plan restrictions. No service output or account credentials are bundled. |
| Video/audio processing | [FFmpeg](https://ffmpeg.org/legal.html) | Installed separately; license depends on build configuration. |
| Rendering and measurements | [Pillow](https://github.com/python-pillow/Pillow), [NumPy](https://github.com/numpy/numpy) | Installed through the package manager, with their respective upstream licenses. |
| Optional speech timing | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Installed separately; follow upstream code/model terms. |

The public repository contains a fresh history with an explicit file list. Model weights, runtime environments, API keys, private voice references, production news files and client materials are excluded.

Font download sources and SHA-256 values are recorded in `fonts/sources.json`. Demo audio and video hashes appear in the example's manifests and release verification.
