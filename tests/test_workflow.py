from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import wave
from unittest.mock import patch

import numpy as np
from magicreels.pipeline import (SR, checked_path, digest, fit_text, frame_hashes, load,
                                mix_samples, new_output, render, save, validate)
from magicreels.tts import ANNOTATION, assemble, prepare_breezy, split_script

ROOT = Path(__file__).resolve().parents[1]


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.voice = np.sin(np.arange(SR * 2) * 2 * np.pi * 440 / SR) * .1
        with wave.open(str(self.root / 'narration.wav'), 'wb') as audio:
            audio.setparams((1, 2, SR, 0, 'NONE', ''))
            audio.writeframes((self.voice * 32767).astype('<i2').tobytes())
        save(self.root / 'audio-map.json', {'master': 'narration.wav', 'master_sha256': digest(self.root / 'narration.wav'),
            'duration': 2, 'parts': [{'part': 1, 'start': 0, 'end': 1, 'display': '第一句。'},
                                   {'part': 2, 'start': 1, 'end': 2, 'display': '第二句。'}]})
        save(self.root / 'approval.json', {'human_audition': 'approved', 'audio_sha256': digest(self.root / 'narration.wav')})
        self.plan = {'schema_version': 1, 'title': '測試', 'audio_map': 'audio-map.json', 'approval': 'approval.json',
            'captions': ['第一句。', '第二句。'], 'hook': {'lead': '一段聲音', 'question': '如何成片？', 'end_part': 1},
            'scenes': [{'kind': 'card', 'parts': [1], 'source_asset_id': 'original:1', 'title': '第一張', 'body': '第一個步驟', 'credit': '自行製圖'},
                       {'kind': 'card', 'parts': [2], 'source_asset_id': 'original:2', 'title': '第二張', 'body': '第二個步驟', 'credit': '自行製圖'}]}
        self.plan_path = self.root / 'project.json'
        save(self.plan_path, self.plan)

    def validate(self):
        save(self.plan_path, self.plan)
        return validate(self.plan_path, ROOT / 'fonts')

    def test_valid_plan(self):
        self.assertEqual(len(self.validate()[3]), 2)

    def test_repeated_source_and_identical_card_rejected(self):
        self.plan['scenes'][1]['source_asset_id'] = 'original:1'
        with self.assertRaisesRegex(ValueError, '唯一'):
            self.validate()
        self.plan['scenes'][1].update(source_asset_id='original:2', title='第一張', body='第一個步驟')
        with self.assertRaisesRegex(ValueError, '相同素材'):
            self.validate()

    def test_skipped_or_non_contiguous_part_rejected(self):
        self.plan['scenes'][1]['parts'] = [1]
        with self.assertRaisesRegex(ValueError, '涵蓋'):
            self.validate()
        self.plan['scenes'][1]['parts'] = [999999999999]
        with self.assertRaisesRegex(ValueError, '範圍'):
            self.validate()

    def test_wrong_or_overflowing_caption_rejected(self):
        self.plan['captions'][0] = '改稿。'
        with self.assertRaisesRegex(ValueError, '正常稿'):
            self.validate()
        from magicreels.pipeline import font
        with self.assertRaisesRegex(ValueError, '超出'):
            fit_text('字' * 15, font(ROOT / 'fonts'))

    def test_control_codes_and_traversal_rejected(self):
        self.plan['hook']['lead'] = r'{\pos(1,1)}'
        with self.assertRaisesRegex(ValueError, '控制'):
            self.validate()
        with self.assertRaisesRegex(ValueError, '目錄內'):
            checked_path(self.root, '../outside.wav')

    def test_audio_approval_bound_to_actual_hash(self):
        save(self.root / 'approval.json', {'human_audition': 'approved', 'audio_sha256': 'stale'})
        with self.assertRaisesRegex(ValueError, '試聽'):
            self.validate()
        data = load(self.root / 'audio-map.json')
        data['duration'] = float('nan')
        save(self.root / 'audio-map.json', data)
        with self.assertRaisesRegex(ValueError, '長度'):
            self.validate()

    def test_output_never_overwrites(self):
        marker = self.root / 'approved.txt'
        marker.write_text('keep')
        with self.assertRaises(FileExistsError):
            new_output(self.root)
        self.assertEqual(marker.read_text(), 'keep')

    def test_mixing_preserves_voice_and_margin(self):
        voice = np.repeat(self.voice[:, None], 2, axis=1)
        music = np.cos(np.arange(len(voice)) * 2 * np.pi * 220 / SR) * .4
        music = np.repeat(music[:, None], 2, axis=1)
        mixed, bed, report = mix_samples(voice, music)
        self.assertLess(np.max(np.abs(mixed - bed - voice)), 1e-12)
        self.assertGreaterEqual(report['min_active_1s_gap_db'], 12 - 1e-8)
        with self.assertRaisesRegex(ValueError, '長度不足'):
            mix_samples(voice, music[:SR])
        with self.assertRaisesRegex(ValueError, '靜音'):
            mix_samples(voice, np.zeros_like(music))
        with self.assertRaisesRegex(ValueError, '人聲峰值'):
            mix_samples(voice * 10, music)

    def test_material_download_rejects_untrusted_host_before_network(self):
        from magicreels.materials import fetch
        video = {'video_files': [{'file_type': 'video/mp4', 'width': 1280, 'height': 720,
                                 'link': 'https://example.org/private.mp4'}]}
        with patch('magicreels.materials.api', return_value=video), patch('magicreels.materials.urlopen') as network:
            with self.assertRaisesRegex(ValueError, 'Pexels'):
                fetch(123, self.root / 'download')
            network.assert_not_called()

    def test_pronunciation_and_sentence_boundaries(self):
        text = '收聽與聽。版本 9.2！'
        spoken, changes, _ = prepare_breezy(text, {'聽': '聽[:ㄊㄧㄥ4]', '收聽': '收聽[:ㄊㄧㄥ1]'})
        self.assertEqual(ANNOTATION.sub('', spoken), text)
        self.assertEqual(len(changes), 2)
        self.assertEqual(split_script(text), ['收聽與聽。', '版本 9.2！'])
        for bad in ({'擊': '吉'}, {'好': '好[:hao3]'}, [], {'': '空白'}):
            with self.assertRaises(ValueError):
                prepare_breezy('測試', bad)

    def test_assembled_audio_and_portable_map(self):
        out = self.root / 'assembled'
        (out / 'raw').mkdir(parents=True)
        result = assemble([self.root / 'narration.wav'], ['測試。'], out)
        self.assertEqual(result['master'], 'narration.wav')
        with wave.open(str(out / 'narration.wav')) as wav:
            master = wav.readframes(wav.getnframes())
        with wave.open(str(out / result['parts'][0]['source'])) as wav:
            self.assertEqual(master, wav.readframes(wav.getnframes()))

    def test_render_smoke_and_decode(self):
        final = render(self.plan_path, ROOT / 'fonts', self.root / 'render')
        report = load(final.parent / 'verification.json')
        self.assertEqual(report['full_decode'], 'pass')
        self.assertLessEqual(report['av_tail_difference'], 1 / 30 + .002)
        self.assertEqual(len(frame_hashes(final)), 60)

    def test_image_and_video_shots_render_without_looping(self):
        from PIL import Image
        from magicreels.pipeline import run
        Image.new('RGB', (320, 180), '#224466').save(self.root / 'photo.png')
        run(['ffmpeg', '-v', 'error', '-n', '-f', 'lavfi', '-i', 'testsrc2=size=320x180:rate=30:duration=3',
             '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(self.root / 'clip.mp4')])
        self.plan['scenes'][0].update(kind='image', path='photo.png', reviewed=True, source_page='original:test-photo')
        self.plan['scenes'][1].update(kind='video', path='clip.mp4', source_in=.5, reviewed=True, source_page='original:test-video')
        save(self.plan_path, self.plan)
        final = render(self.plan_path, ROOT / 'fonts', self.root / 'media-render')
        self.assertEqual(len(frame_hashes(final)), 60)
        self.plan['scenes'][1]['source_in'] = 2.5
        with self.assertRaisesRegex(ValueError, '不足'):
            self.validate()


if __name__ == '__main__':
    unittest.main()
