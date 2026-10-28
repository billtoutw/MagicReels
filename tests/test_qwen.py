import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
import wave

import numpy as np

from magicreels.qwen import SAMPLE_RATE, finish_audio, load_qwen, main, prepare_qwen
from magicreels.tts import assemble


class QwenTests(unittest.TestCase):
    def test_phonetics_stay_separate_and_respect_english_boundaries(self):
        text = "2 兆與預期、同期。Claude / ClaudeAPI / claude。"
        spoken, changes, _ = prepare_qwen(text, {"2 兆": "兩兆", "預期": "育奇", "同期": "同旗", "Claude": "Cloud"})
        self.assertEqual(spoken, "兩兆與育奇、同旗。Cloud / ClaudeAPI / claude。")
        self.assertEqual(len(changes), 4)
        self.assertEqual(text[changes[1]['start']:changes[1]['end']], '預期')
        self.assertIn('預期', text)
        self.assertEqual(prepare_qwen('預期', {})[0], '預期')

    def test_rejects_empty_aliases_controls_and_sentence_changes(self):
        for bad in ([], {'': '好'}, {'好': ''}, {'好': '  '}, {'好': None},
                    {'好': '好。'}, {'好': '好\n'}, {'好': '好[:ㄏㄠ3]'},
                    {'好': '<|audio|>'}, {'好': '{x}'}, {'好。': '好'}, {'好': '\\N'}):
            with self.subTest(rule=bad), self.assertRaises(ValueError):
                prepare_qwen('好', bad)

    def test_constant_gain_preserves_interior_and_bounds_peak(self):
        from types import SimpleNamespace
        meter = SimpleNamespace(integrated_loudness=lambda _: -30)
        original = np.sin(np.arange(SAMPLE_RATE) * 2 * np.pi * 220 / SAMPLE_RATE) * .9
        audio, stats = finish_audio(original, meter)
        gain = 10 ** (stats['gain_db'] / 20)
        np.testing.assert_allclose(audio[120:SAMPLE_RATE-120], original[120:-120] * gain)
        np.testing.assert_array_equal(audio[SAMPLE_RATE:], np.zeros(3600))
        self.assertEqual(len(audio), SAMPLE_RATE + 3600)
        self.assertLessEqual(max(abs(audio)), 10 ** (-1.5 / 20) + 1e-12)
        self.assertEqual(audio[0], 0)
        self.assertEqual(audio[SAMPLE_RATE-1], 0)
        for bad in (np.zeros(SAMPLE_RATE), np.full(SAMPLE_RATE, np.nan), np.ones(2), np.ones((1, SAMPLE_RATE))):
            with self.assertRaises(ValueError):
                finish_audio(bad, meter)

    def test_pcm_assembly_keeps_24_bit_samples_and_real_boundaries(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'raw').mkdir()
            paths, pieces = [], []
            for i, seconds in enumerate((1, 2), 1):
                path = out / f'{i:03}.wav'
                pcm = b'\x01\x02\x03' * SAMPLE_RATE * seconds
                with wave.open(str(path), 'wb') as wav:
                    wav.setparams((1, 3, SAMPLE_RATE, 0, 'NONE', ''))
                    wav.writeframes(pcm)
                paths.append(path)
                pieces.append(pcm)
            result = assemble(paths, ['第一句。', '第二句。'], out, preserve_pcm=True)
            with wave.open(str(out / result['master']), 'rb') as wav:
                self.assertEqual(wav.getparams()[:3], (1, 3, SAMPLE_RATE))
                self.assertEqual(wav.readframes(wav.getnframes()), b''.join(pieces))
            for path, pcm in zip(paths, pieces):
                with wave.open(str(path), 'rb') as wav:
                    self.assertEqual(wav.readframes(wav.getnframes()), pcm)
            self.assertEqual(result['duration'], 3)
            self.assertEqual(result['parts'][1]['start'], 1)
            self.assertEqual(result['human_audition'], 'pending')

    def test_incompatible_pcm_formats_rejected(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            paths = [root / 'a.wav', root / 'b.wav']
            for path, sr in zip(paths, (24000, 44100)):
                with wave.open(str(path), 'wb') as wav:
                    wav.setparams((1, 2, sr, 0, 'NONE', ''))
                    wav.writeframes(b'\0\0' * sr)
            with self.assertRaisesRegex(ValueError, '相同格式'):
                assemble(paths, ['一', '二'], root, preserve_pcm=True)

    def test_other_platform_stops_before_import_or_download(self):
        with patch('magicreels.qwen.platform.system', return_value='Linux'):
            with self.assertRaisesRegex(RuntimeError, 'Apple Silicon'):
                load_qwen()

    def test_invalid_reference_records_failure_without_model_load(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            reference = root / 'input.wav'
            with wave.open(str(reference), 'wb') as wav:
                wav.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', ''))
                wav.writeframes(b'\0\0' * SAMPLE_RATE)
            transcript = root / 'input.txt'
            transcript.write_text('參考聲音。')
            out = root / 'voice'
            args = ['magicreels-qwen', '--text', '測試。', '--reference', str(reference),
                    '--reference-text', str(transcript), '--out', str(out)]
            with patch('sys.argv', args), patch('magicreels.qwen.load_qwen') as loader:
                with self.assertRaisesRegex(ValueError, '3–30'):
                    main()
                loader.assert_not_called()
                self.assertEqual(json.loads((out / 'failure.json').read_text())['error_type'], 'ValueError')
                self.assertFalse((out / 'audio-map.json').exists())
                with self.assertRaises(FileExistsError):
                    main()


if __name__ == '__main__':
    unittest.main()
