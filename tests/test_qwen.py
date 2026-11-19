import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import wave

import numpy as np

from magicreels.qwen import SAMPLE_RATE, finish_audio, load_qwen, main, plan_segments, prepare_qwen
from magicreels.tts import assemble
from magicreels.voicestudio import load_voicestudio


class QwenTests(unittest.TestCase):
    def test_voicestudio_loads_the_resolved_local_checkpoint(self):
        checkpoint = Path('/local/checkpoint')
        backend = SimpleNamespace(supports_cloning=True, sample_rate=SAMPLE_RATE)
        factory = Mock(return_value=backend)
        with patch.dict(os.environ), \
             patch.dict(sys.modules, {'services.tts_backend': SimpleNamespace(MLXAudioBackend=factory)}), \
             patch('magicreels.voicestudio.resolve_checkpoint', return_value=checkpoint):
            self.assertEqual(load_voicestudio(), (backend, checkpoint))
            self.assertEqual(os.environ['OMNIVOICE_MLX_AUDIO_MODEL'], str(checkpoint))
            backend.sample_rate = 44100
            with self.assertRaises(ValueError):
                load_voicestudio()

    def test_semantic_blocks_keep_sentences_and_line_wraps_together(self):
        blocks = ['版本 9.2 有什麼改變？\n第一個改變是速度。第二個是容量！',
                  '接著說明成本。最後回到使用情境。']
        text = '\r\n'.join(blocks)
        rows = plan_segments(text, {}, blocks)
        self.assertEqual([row['synthesis'] for row in rows], blocks)
        self.assertEqual([row['part'] for row in rows], [1, 2])

    def test_plan_rejects_missing_reordered_changed_and_oversized_text(self):
        text = '先確認原因。接著說明影響。'
        for bad in ([], {}, [''], [None], ['先確認原因。'],
                    ['接著說明影響。', '先確認原因。'], ['先確認結果。接著說明影響。']):
            with self.subTest(plan=bad), self.assertRaises(ValueError):
                plan_segments(text, {}, bad)
        for dictionary, block in (({}, '甲。' * 61), ({'好': '好' * 121}, '好')):
            with self.assertRaisesRegex(ValueError, '120'):
                plan_segments(block, dictionary, [block])

    def test_script_requires_plan_before_model_load_or_output(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp) / 'voice'
            args = ['magicreels-qwen', '--script', 'script.txt', '--out', str(out),
                    '--reference', 'ref.wav', '--reference-text', 'ref.txt']
            with patch('sys.argv', args), patch('magicreels.qwen.load_qwen') as loader, \
                 patch('sys.stderr'), self.assertRaises(SystemExit) as error:
                main()
            self.assertEqual(error.exception.code, 2)
            loader.assert_not_called()
            self.assertFalse(out.exists())

    def test_plan_only_preserves_source_bytes_without_reference_or_model_access(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = '預期會改善。\r\n接著比較同期。\r\n'.encode('utf-8')
            script = root / 'script.txt'
            script.write_bytes(original)
            segments = root / 'segments.json'
            segments.write_text(json.dumps(['預期會改善。接著比較同期。']))
            rules = root / 'rules.json'
            rules.write_text(json.dumps({'預期': '育奇'}))
            out = root / 'plan'
            args = ['magicreels-qwen', '--script', str(script), '--segments', str(segments),
                    '--pronunciations', str(rules), '--plan-only', '--out', str(out),
                    '--reference', 'unused.wav', '--reference-text', 'unused.txt']
            with patch('sys.argv', args), patch('magicreels.qwen.load_qwen') as loader:
                main()
            loader.assert_not_called()
            self.assertEqual((out / 'display-script.txt').read_bytes(), original)
            plan = json.loads((out / 'generation-plan.json').read_text())
            self.assertEqual(plan['segment_count'], 1)
            self.assertEqual(plan['segments'][0]['synthesis'], '育奇會改善。接著比較同期。')
            self.assertFalse((out / 'narration.wav').exists())

    def test_model_receives_whole_blocks_once_without_sentence_splitting(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            blocks = ['先說明原因。再說明影響？最後回到重點！', '這是另一段。語調需要延續。']
            script = root / 'script.txt'
            script.write_text('\n'.join(blocks))
            segments = root / 'segments.json'
            segments.write_text(json.dumps(blocks))
            reference = root / 'reference.wav'
            with wave.open(str(reference), 'wb') as wav:
                wav.setparams((1, 2, SAMPLE_RATE, 0, 'NONE', ''))
                wav.writeframes(b'\0\0' * SAMPLE_RATE * 3)
            transcript = root / 'reference.txt'
            transcript.write_text('參考錄音。')
            (root / 'config.json').write_text('{}')
            model = Mock()
            model.generate.side_effect = lambda *a, **k: [SimpleNamespace(audio=np.zeros(SAMPLE_RATE), sample_rate=SAMPLE_RATE)]
            mx = SimpleNamespace(random=SimpleNamespace(seed=lambda _: None), clear_cache=lambda: None)
            sf = SimpleNamespace(write=lambda path, *a, **k: Path(path).write_bytes(b'mocked-wave'))
            modules = {'mlx': SimpleNamespace(core=mx), 'mlx.core': mx, 'soundfile': sf,
                       'pyloudnorm': SimpleNamespace(Meter=lambda _: None)}
            out = root / 'voice'
            args = ['magicreels-qwen', '--script', str(script), '--segments', str(segments),
                    '--reference', str(reference), '--reference-text', str(transcript), '--out', str(out)]
            with patch('sys.argv', args), patch.dict(sys.modules, modules), \
                 patch('magicreels.qwen.load_qwen', return_value=(model, root)), \
                 patch('magicreels.qwen.finish_audio', return_value=(np.zeros(SAMPLE_RATE), {})), \
                 patch('magicreels.qwen.assemble', return_value={'parts': [{}, {}]}), \
                 patch('magicreels.qwen.importlib.metadata.version', return_value='test'):
                main()
            self.assertEqual([call.args[0] for call in model.generate.call_args_list], blocks)
            result = json.loads((out / 'audio-map.json').read_text())
            self.assertEqual(result['generation_segment_count'], 2)
            self.assertIn('generation_plan_sha256', result)

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
