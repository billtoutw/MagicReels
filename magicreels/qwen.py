"""Qwen3-TTS 1.7B Base voice cloning on Apple Silicon through MLX Audio."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import wave

import numpy as np

from .tts import assemble, prepare, sha256, split_script, write_json

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
MODEL_REVISION = "a6eb4f68e4b056f1215157bb696209bc82a6db48"
SAMPLE_RATE = 24000
SEED = 42


def prepare_qwen(text, dictionary):
    if not isinstance(dictionary, dict):
        raise ValueError("讀音字典必須是文字對文字的 JSON 物件。")
    rules = []
    for original, replacement in dictionary.items():
        if any(not isinstance(s, str) or not s.strip() or
               any(c in s for c in "\n\r。！？!?{}\\") or "[:" in s or "<|" in s
               for s in (original, replacement)):
            raise ValueError("Qwen 讀音字典須為非空字詞，不含斷句、注音標記或控制字元。")
        rules.append({"display": original, "synthesis": replacement})
    return prepare(text, rules)


def finish_audio(audio, meter):
    audio = np.asarray(audio, dtype=np.float64)
    if audio.ndim != 1 or not SAMPLE_RATE // 2 <= audio.size <= SAMPLE_RATE * 50 or not np.isfinite(audio).all():
        raise ValueError("模型音訊須為有限數值的單聲道，且長度介於 0.5–50 秒。")
    peak = float(np.max(np.abs(audio)))
    level = float(meter.integrated_loudness(audio))
    if peak <= 0 or not np.isfinite(level):
        raise ValueError("模型輸出為靜音或響度無效，請檢查參考錄音及稿件。")
    # The approved workflow uses constant gain to retain phrasing and dynamics.
    gain_db = min(-23.1 - level, -1.5 - 20 * np.log10(peak))
    audio = audio * 10 ** (gain_db / 20)
    fade = round(SAMPLE_RATE * .005)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    audio = np.pad(audio, (0, round(SAMPLE_RATE * .15)))
    if not np.isfinite(audio).all() or np.max(np.abs(audio)) >= 1:
        raise ValueError("音訊峰值超出範圍。")
    return audio, {"gain_db": float(gain_db), "target_lufs": -23.1,
                   "measured_lufs": float(meter.integrated_loudness(audio)),
                   "edge_fade_ms": 5, "tail_silence_ms": 150, "clipped_samples": 0}


def load_qwen(model_path=None):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        raise RuntimeError("此入口使用 macOS Apple Silicon；其他平台可使用已生成的音檔製片。")
    from huggingface_hub import snapshot_download
    from mlx_audio.tts.utils import load_model
    path = model_path or Path(snapshot_download(MODEL_ID, revision=MODEL_REVISION))
    if not path.is_dir():
        raise FileNotFoundError(path)
    config = json.loads((path / "config.json").read_text(encoding="utf-8"))
    if config.get("tts_model_type") != "base" or config.get("tts_model_size") != "1b7" or config.get("quantization"):
        raise ValueError("請使用 Qwen3-TTS 1.7B Base BF16 模型。")
    model = load_model(str(path))
    if model.tokenizer is None or model.speech_tokenizer is None or not model.speech_tokenizer.has_encoder:
        raise ValueError("聲線複製需要完整 tokenizer encoder，請補齊模型檔案。")
    return model, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--script", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reference-text", type=Path, required=True)
    parser.add_argument("--pronunciations", type=Path)
    parser.add_argument("--model", type=Path, help="Optional existing local BF16 model directory")
    args = parser.parse_args()
    original = args.script.read_bytes() if args.script else (args.text + "\n").encode("utf-8")
    text = original.decode("utf-8")
    if any(s in text for s in ("[:", "<|", "{", "}", "\\")):
        parser.error("請輸入正常稿，讀音替換放入讀音字典。")
    displays = split_script(text)
    dictionary = json.loads(args.pronunciations.read_text(encoding="utf-8")) if args.pronunciations else {}
    synthesis, changes, _ = prepare_qwen(text, dictionary)
    parts = split_script(synthesis)
    if len(parts) != len(displays):
        raise ValueError("讀音處理改變了分段，請檢查字典。")
    reference_text = args.reference_text.read_text(encoding="utf-8").strip()
    if not reference_text:
        raise ValueError("參考逐字稿不能空白。")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    (out / "display-script.txt").write_bytes(original)
    (out / "synthesis-input.txt").write_text(synthesis, encoding="utf-8")
    write_json(out / "pronunciation-map.json", {"changes": changes})
    started = time.monotonic()
    try:
        prompt = out / "reference.wav"
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-n", "-i", str(args.reference.resolve()),
                        "-ac", "1", "-ar", str(SAMPLE_RATE), "-c:a", "pcm_s16le", str(prompt)], check=True)
        with wave.open(str(prompt), "rb") as wav:
            if not 3 <= wav.getnframes() / wav.getframerate() <= 30:
                raise ValueError("參考錄音請保留 3–30 秒的完整語句。")
        (out / "reference.txt").write_text(reference_text + "\n", encoding="utf-8")
        os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
        os.environ.setdefault("NUMBA_CACHE_DIR", str(out / "numba-cache"))
        model, model_path = load_qwen(args.model)
        import mlx.core as mx
        import pyloudnorm as pyln
        import soundfile as sf

        meter = pyln.Meter(SAMPLE_RATE)
        paths, measurements = [], []
        for i, spoken in enumerate(parts, 1):
            mx.random.seed(SEED)
            np.random.seed(SEED)
            chunks = list(model.generate(spoken, ref_audio=str(prompt), ref_text=reference_text,
                                        lang_code="Chinese", max_tokens=640, stream=False))
            if not chunks or any(c.sample_rate != SAMPLE_RATE for c in chunks):
                raise ValueError("模型未產生預期的 24 kHz 音訊。")
            audio = np.concatenate([np.asarray(c.audio, dtype=np.float32).reshape(-1) for c in chunks])
            raw = out / "raw" / f"{i:03}.wav"
            sf.write(raw, audio, SAMPLE_RATE, subtype="FLOAT")
            audio, measurement = finish_audio(audio, meter)
            path = out / f"{i:03}.wav"
            sf.write(path, audio, SAMPLE_RATE, subtype="PCM_24")
            paths.append(path)
            measurements.append({**measurement, "raw_sha256": sha256(raw)})
            print(f"完成 {i}/{len(parts)} 段", flush=True)
            mx.clear_cache()
        record = assemble(paths, displays, out, preserve_pcm=True)
        for part, measurement in zip(record["parts"], measurements):
            part.update(measurement)
        record.update(engine="Qwen3-TTS 1.7B Base BF16", mlx_audio=importlib.metadata.version("mlx-audio"),
                      model_id=MODEL_ID, model_revision=MODEL_REVISION if args.model is None else None,
                      model_config_sha256=sha256(model_path / "config.json"), seed=SEED,
                      process_seconds=time.monotonic() - started, reference_sha256=sha256(args.reference),
                      prepared_reference_sha256=sha256(prompt), reference_text_sha256=sha256(out / "reference.txt"),
                      voicebox_required=False, generation_fallback=False)
        write_json(out / "audio-map.json", record)
    except Exception as error:
        write_json(out / "failure.json", {"error_type": type(error).__name__,
                   "action": "保留已完成片段；修正原因後使用新輸出目錄。"})
        raise
    print(f"試聽：{out / 'narration.mp3'}", flush=True)


if __name__ == "__main__":
    main()
