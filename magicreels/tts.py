"""Local BreezyVoice narration. Derived from the Reelsturbo production workflow."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import wave

ANNOTATION = re.compile(r"\[:[\u3105-\u312f]+[1-5]\]")
SAMPLE_RATE = 44100

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def split_script(text):
    parts = [part.strip() for part in re.split(r"(?<=[。！？!?])|\n+", text) if part.strip()]
    if not parts:
        raise ValueError("稿件不能空白。")
    for i, part in enumerate(parts, 1):
        counted = ANNOTATION.sub("", part)
        if len(counted) > 120:
            raise ValueError(f"第 {i} 段超過 120 字，請加上句號或分行。")
    return parts

def prepare(source, rules):
    by_word = {r["display"]: r for r in rules}
    patterns = []
    for word in sorted(by_word, key=len, reverse=True):
        escaped = re.escape(word)
        if word.isascii():
            escaped = r"(?<![A-Za-z0-9_])" + escaped + r"(?![A-Za-z0-9_])"
        patterns.append(escaped)
    changes = []
    def replace(match):
        rule = by_word[match.group()]
        changes.append({**rule, "start": match.start(), "end": match.end()})
        return rule["synthesis"]
    return (re.sub("|".join(patterns), replace, source) if patterns else source), changes, []


def prepare_breezy(text, dictionary):
    if not isinstance(dictionary, dict):
        raise ValueError("讀音字典必須是文字對文字的 JSON 物件。")
    rules = []
    for original, replacement in dictionary.items():
        if not isinstance(original, str) or not original.strip() or not isinstance(replacement, str):
            raise ValueError("讀音字典的字詞及替換內容必須是非空白文字。")
        if ANNOTATION.sub("", replacement) != original or "[:" in original or "<|" in replacement:
            raise ValueError(f"讀音規則須保留原字，只加入注音：{original}")
        rules.append({"display": original, "synthesis": replacement})
    return prepare(text, rules)

def init_breezy(runtime):
    for key, value in {
        "HF_HOME": runtime / "cache/huggingface", "XDG_CACHE_HOME": runtime / "cache",
        "MPLCONFIGDIR": runtime / "cache/matplotlib", "NUMBA_CACHE_DIR": runtime / "cache/numba",
        "TORCH_HOME": runtime / "cache/torch",
    }.items():
        os.environ[key] = str(value)
    os.environ["PYTHONUTF8"] = "1"
    sys.path.insert(0, str(runtime / "upstream"))
    from single_inference import CustomCosyVoice, single_inference
    from g2pw import G2PWConverter
    import torch

    torch.set_num_threads(4)
    model = CustomCosyVoice(str(runtime / "models/BreezyVoice"))
    converter = G2PWConverter(model_dir=str(runtime / "upstream/G2PWModel"))
    # Avoid spawning new Python workers for every short sentence on macOS.
    converter.num_workers = 0
    return model, converter, single_inference

def assemble(raw_paths, displays, out):
    if not raw_paths or len(raw_paths) != len(displays):
        raise ValueError("每個正常稿句段須對應一個音檔。")
    pieces, counts = [], []
    for path in raw_paths:
        pcm = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path),
            "-ar", str(SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"])
        if len(pcm) < SAMPLE_RATE // 2:
            raise ValueError(f"音檔過短：{path.name}")
        pieces.append(pcm)
        counts.append(len(pcm) // 2)
    raw_master = out / "raw/narration.wav"
    with wave.open(str(raw_master), "wb") as wav:
        wav.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
        wav.writeframes(b"".join(pieces))
    master, delivery = out / "narration.wav", out / "narration.mp3"
    filters = (f"loudnorm=I=-16:TP=-1.5:LRA=11,aresample={SAMPLE_RATE},"
               f"apad=whole_len={sum(counts)},atrim=end_sample={sum(counts)}")
    subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(raw_master), "-af", filters,
                    "-ar", str(SAMPLE_RATE), "-ac", "1", "-c:a", "pcm_s16le", str(master)], check=True)
    with wave.open(str(master), "rb") as wav:
        assert wav.getparams()[:3] == (1, 2, SAMPLE_RATE)
        pcm = wav.readframes(wav.getnframes())
    assert len(pcm) == sum(counts) * 2
    timeline, offset = [], 0
    for i, (count, text) in enumerate(zip(counts, displays), 1):
        path = out / f"{i:03}.wav"
        part = pcm[offset * 2:(offset + count) * 2]
        with wave.open(str(path), "wb") as wav:
            wav.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
            wav.writeframes(part)
        timeline.append({"part": i, "source": path.name, "display": text,
                         "start": offset / SAMPLE_RATE, "end": (offset + count) / SAMPLE_RATE,
                         "samples": count, "pcm_sha256": hashlib.sha256(part).hexdigest()})
        offset += count
    subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(master),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(delivery)], check=True)
    for audio in (master, delivery):
        subprocess.run(["ffmpeg", "-v", "error", "-i", str(audio), "-f", "null", "-"], check=True)
    return {"master": master.name, "delivery": delivery.name, "duration": offset / SAMPLE_RATE,
            "sample_rate": SAMPLE_RATE, "channels": 1, "parts": timeline,
            "master_sha256": sha256(master), "delivery_sha256": sha256(delivery),
            "full_decode": "pass", "postprocessing": filters, "speed": 1,
            "human_audition": "pending"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--script", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reference-text", type=Path, required=True)
    parser.add_argument("--pronunciations", type=Path)
    args = parser.parse_args()
    original = args.script.read_bytes() if args.script else (args.text + "\n").encode("utf-8")
    text = original.decode("utf-8")
    if "[:" in text or "<|" in text:
        parser.error("請輸入正常稿，讀音標記放入讀音字典。")
    displays = split_script(text)
    dictionary = json.loads(args.pronunciations.read_text()) if args.pronunciations else {}
    synthesis, changes, _ = prepare_breezy(text, dictionary)
    parts = split_script(synthesis)
    if len(parts) != len(displays):
        raise ValueError("讀音處理改變了分段，請檢查字典。")
    runtime = args.runtime.resolve()
    reference_text = args.reference_text.read_text(encoding="utf-8").strip()
    if not reference_text:
        raise ValueError("參考逐字稿不能空白。")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "raw").mkdir()
    (out / "display-script.txt").write_bytes(original)
    (out / "synthesis-input.txt").write_text(synthesis, encoding="utf-8")
    write_json(out / "pronunciation-map.json", {"changes": changes})
    prompt = out / "reference.wav"
    subprocess.run(["ffmpeg", "-v", "error", "-n", "-i", str(args.reference.resolve()),
                    "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(prompt)], check=True)
    with wave.open(str(prompt), "rb") as wav:
        seconds = wav.getnframes() / wav.getframerate()
    if not 3 <= seconds <= 30:
        raise ValueError("參考錄音請保留 3–30 秒的完整語句。")
    (out / "reference.txt").write_text(reference_text + "\n", encoding="utf-8")
    started = time.monotonic()
    try:
        print("載入本機 BreezyVoice。", flush=True)
        model, converter, infer = init_breezy(runtime)
        import torch
        raw_paths = []
        for i, spoken in enumerate(parts, 1):
            path = out / "raw" / f"{i:03}.wav"
            with torch.inference_mode():
                infer(str(prompt), spoken, str(path), model, converter, reference_text)
            raw_paths.append(path)
            print(f"完成 {i}/{len(parts)} 段", flush=True)
        record = assemble(raw_paths, displays, out)
    except Exception as error:
        write_json(out / "failure.json", {"error_type": type(error).__name__,
                   "action": "保留已完成片段；修正原因後使用新輸出目錄。"})
        raise
    record.update(engine="breezy", process_seconds=time.monotonic() - started,
                  reference_sha256=sha256(args.reference),
                  upstream_commit="d592c9d3e8927a0f53f68616387060dcd32a05ea",
                  model_revision="e33b502e0ac21c16b0ee0d00df66ac3fa737393d")
    write_json(out / "audio-map.json", record)
    print(f"試聽：{out / 'narration.mp3'}", flush=True)


if __name__ == "__main__":
    main()
