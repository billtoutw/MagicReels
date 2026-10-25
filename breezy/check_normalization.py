"""Regression checks for the official fallback normalizer on macOS."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
os.environ["HF_HOME"] = str(ROOT / "cache/huggingface")
os.environ["MPLCONFIGDIR"] = str(ROOT / "cache/matplotlib")
os.environ["XDG_CACHE_HOME"] = str(ROOT / "cache")
sys.path.insert(0, str(ROOT / "upstream"))
from single_inference import CustomCosyVoiceFrontEnd
from tn.chinese.normalizer import Normalizer
from tn.english.normalizer import Normalizer as EnglishNormalizer
import inflect

frontend = CustomCosyVoiceFrontEnd.__new__(CustomCosyVoiceFrontEnd)
frontend.use_ttsfrd = False
frontend.zh_tn_model = Normalizer(remove_erhua=False, full_to_half=False)
frontend.en_tn_model = EnglishNormalizer()
frontend.inflect_parser = inflect.engine()

for source, expected in (
    ("歡迎收聽這段配音。", "歡迎收聽這段配音"),
    ("歡迎收聽[:ㄊㄧㄥ1]這段配音。", "歡迎收聽[:ㄊㄧㄥ1]這段配音"),
    ("今天天氣真好[:ㄏㄠ3]。", "今天天氣真好[:ㄏㄠ3]"),
):
    actual = frontend.text_normalize_new(source, split=False)
    assert expected in actual, (source, actual)
    print(actual)
print("Normalization checks: pass")
