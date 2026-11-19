"""VoiceStudio's local MLX Audio backend with MagicReels audio outputs."""
import os

from .qwen import SAMPLE_RATE, main as generate, resolve_checkpoint


def load_voicestudio(model_path=None):
    try:
        from services.tts_backend import MLXAudioBackend
    except ModuleNotFoundError as exc:
        if exc.name not in ("services", "services.tts_backend"):
            raise
        raise RuntimeError("請依 docs/voicestudio.md 設定 VoiceStudio 原始碼路徑與本機環境。") from exc

    path = resolve_checkpoint(model_path)
    os.environ["OMNIVOICE_MLX_AUDIO_MODEL"] = str(path)
    backend = MLXAudioBackend()
    if not backend.supports_cloning or backend.sample_rate != SAMPLE_RATE:
        raise ValueError("VoiceStudio 須使用支援聲線複製的 24 kHz Qwen3-TTS Base 模型。")
    return backend, path


def main():
    generate(backend="voicestudio")


if __name__ == "__main__":
    main()
