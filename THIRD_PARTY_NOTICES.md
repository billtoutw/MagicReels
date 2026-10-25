# Third-party sources and asset provenance

MagicReels code and original documentation are MIT licensed. The components below retain their own terms. A code license does not automatically grant rights to a person's voice, a stock asset, or a hosted service's generated output.

| Component | Source | License / handling |
| --- | --- | --- |
| Workflow origin | [MoneyPrinterTurbo](https://github.com/harry0703/MoneyPrinterTurbo) | MIT. The original Reelsturbo workspace built on this project. MagicReels extracts the editorial workflow and standalone production scripts; it does not redistribute that workspace or its history. |
| Voice inference and weights | [BreezyVoice](https://github.com/mtkresearch/BreezyVoice), [model card](https://huggingface.co/MediaTek-Research/BreezyVoice) | Upstream declares Apache-2.0. Downloaded separately. Pinned source/model revisions are in `docs/breezyvoice.md`. |
| macOS normalizer patch | `breezy/macos-normalization.patch`, derived from BreezyVoice `single_inference.py` | Modified to preserve Traditional Chinese and annotation boundaries. Apache-2.0 text is bundled at `breezy/Apache-2.0.txt`. |
| Demo narration | Generated with BreezyVoice using upstream `data/example.wav` at the pinned commit | Official reference used solely for the openly described demo. The reference recording itself is not bundled. No private personal voice was used. Generated output is not an endorsement by MediaTek Research or the reference speaker. |
| Sans font | [Source Han Sans](https://github.com/adobe-fonts/source-han-sans), unmodified `SourceHanSansTW-Bold.otf` | SIL OFL 1.1, bundled with `fonts/OFL-Sans.txt`. |
| Serif font | [Source Han Serif](https://github.com/adobe-fonts/source-han-serif), unmodified `SourceHanSerifTC-Bold.otf` | SIL OFL 1.1, bundled with `fonts/OFL-Serif.txt`. |
| Demo article, plan and cards | Original MagicReels example | MIT, including rendered original card assets. |
| Demo music | Original score from `examples/first-reel/make_music.py` | MIT. Generated entirely from mathematical oscillators; no sampled recordings or third-party music. |
| Optional stock footage | [Pexels](https://www.pexels.com/license/) | Retrieved by users. No stock footage is bundled. Record original IDs, source pages and creators, and review the current license. |
| Optional music service | [ElevenLabs](https://elevenlabs.io/terms-of-use) | Separate service terms and plan restrictions. No service output or account credentials are bundled. |
| Video/audio processing | [FFmpeg](https://ffmpeg.org/legal.html) | Installed separately; license depends on build configuration. |
| Rendering and measurements | [Pillow](https://github.com/python-pillow/Pillow), [NumPy](https://github.com/numpy/numpy) | Installed through the package manager, with their respective upstream licenses. |
| Optional speech timing | [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | Installed separately; follow upstream code/model terms. |

The public repository contains a fresh history with an explicit file list. Model weights, runtime environments, API keys, private voice references, production news files and client materials are excluded.

Font download sources and SHA-256 values are recorded in `fonts/sources.json`. Demo audio and video hashes appear in the example's manifests and release verification.
