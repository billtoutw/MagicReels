"""A single 1080 x 1920 editorial template and voice-first music mixing."""
from pathlib import Path
import hashlib
import json
import math
import shutil
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS, WIDTH, HEIGHT, SR = 30, 1080, 1920, 48000


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(command, **kwargs):
    result = subprocess.run(command, capture_output=True, **kwargs)
    if result.returncode:
        raise RuntimeError(result.stderr.decode('utf-8', errors='replace')[-3000:])
    return result.stdout


def probe(path):
    return json.loads(run(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(path)]))


def new_output(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def plain(text):
    if not isinstance(text, str) or any(x in text for x in ('{', '}', '\\', '[:', '<|')):
        raise ValueError('顯示文字必須是正常稿，且不得包含 ASS 控制字元。')
    return text


def compact(text):
    return ''.join(text.split())


def checked_path(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f'檔案須位於專案目錄內：{value}')
    return path


def font(root, serif=False, size=90):
    name = 'SourceHanSerifTC-Bold.otf' if serif else 'SourceHanSansTW-Bold.otf'
    return ImageFont.truetype(str(root / name), size)


def fit_text(text, face, max_width=900, max_lines=2):
    lines = plain(text).split('\n')
    if len(lines) > max_lines or any(face.getlength(line) > max_width for line in lines):
        raise ValueError(f'文字超出版面；請依語意換行或縮短段落：{text}')
    return lines


def validate(plan_file, fonts, require_approval=True):
    plan_file, fonts = Path(plan_file).resolve(), Path(fonts).resolve()
    root, plan = plan_file.parent, load(plan_file)
    if plan.get('schema_version') != 1:
        raise ValueError('只支援 schema_version 1。')
    amap_path = checked_path(root, plan['audio_map'])
    amap = load(amap_path)
    audio = checked_path(amap_path.parent, amap['master'])
    if digest(audio) != amap['master_sha256']:
        raise ValueError('旁白雜湊與音訊清單不同，請重新核對版本。')
    duration = float(probe(audio)['format']['duration'])
    if not math.isfinite(duration) or not 1 <= duration <= 180:
        raise ValueError('v0.2 支援 1–180 秒影片。')
    if not math.isfinite(float(amap['duration'])) or abs(float(amap['duration']) - duration) > .03:
        raise ValueError('音訊清單長度與實際音檔不同。')
    if require_approval:
        approval = load(checked_path(root, plan['approval']))
        if approval.get('human_audition') != 'approved' or approval.get('audio_sha256') != digest(audio):
            raise ValueError('請先試聽完整旁白，再保存對應音檔的核准紀錄。')
    parts, captions = amap['parts'], plan['captions']
    if not parts or len(parts) != len(captions):
        raise ValueError('每個旁白段落須有一筆字幕。')
    previous = 0.0
    for i, (part, caption) in enumerate(zip(parts, captions), 1):
        a, b = float(part['start']), float(part['end'])
        if part['part'] != i or not all(map(math.isfinite, (a, b))) or abs(a - previous) > .002 or b <= a:
            raise ValueError('旁白時間表須連續、遞增，從零開始。')
        if compact(caption) != compact(part['display']):
            raise ValueError(f'第 {i} 段字幕與正常稿不同。')
        fit_text(caption, font(fonts))
        previous = b
    if abs(previous - duration) > .03:
        raise ValueError('時間表與音檔長度不同。')
    used_parts, ids, hashes, sources = [], set(), set(), []
    for scene in plan['scenes']:
        sid = scene['source_asset_id']
        if not isinstance(sid, str) or not sid.strip() or sid in ids:
            raise ValueError('每個原始素材須有唯一 source_asset_id；全片只能使用一次。')
        ids.add(sid)
        indexes = scene['parts']
        if not indexes or any(type(i) is not int or not 1 <= i <= len(parts) for i in indexes):
            raise ValueError('素材段落超出旁白範圍。')
        if indexes != list(range(indexes[0], indexes[-1] + 1)):
            raise ValueError('每個素材須連續呈現。')
        used_parts.extend(indexes)
        fit_text(scene['credit'], font(fonts, size=34), 900, 1)
        kind = scene['kind']
        if scene.get('title'):
            fit_text(scene['title'], font(fonts, serif=True, size=96))
        if kind == 'card':
            fit_text(scene['title'], font(fonts, serif=True, size=96))
            fit_text(scene['body'], font(fonts, size=58), 860, 4)
            key = hashlib.sha256((scene['title'] + '\n' + scene['body']).encode()).hexdigest()
        elif kind in ('image', 'video', 'diagram'):
            if scene.get('reviewed') is not True or not scene.get('source_page'):
                raise ValueError('外部素材須保存來源並完成畫面核對。')
            asset = checked_path(root, scene['path'])
            key = digest(asset)
            if kind == 'diagram':
                fit_text(scene['body'], font(fonts, size=58), 860, 2)
            if kind == 'video':
                length = float(probe(asset)['format']['duration'])
                start = float(scene.get('source_in', 0))
                if not math.isfinite(start) or start < 0:
                    raise ValueError('素材取段起點無效。')
                if indexes[-1] > len(parts) or indexes[0] < 1:
                    raise ValueError('素材段落超出旁白範圍。')
                needed = parts[indexes[-1] - 1]['end'] - parts[indexes[0] - 1]['start']
                if start + needed > length - 1 / FPS:
                    raise ValueError('來源影片不足以涵蓋分鏡，請補找素材。')
        else:
            raise ValueError('素材類型須為 card、image、diagram 或 video。')
        if key in hashes:
            raise ValueError('偵測到相同素材內容，請使用其他素材。')
        hashes.add(key)
        sources.append({'source_asset_id': sid, 'sha256': key, 'parts': indexes,
                        'credit': scene['credit'], 'source_page': scene.get('source_page', 'original')})
    if used_parts != list(range(1, len(parts) + 1)):
        raise ValueError('分鏡須依序涵蓋全部旁白，且不得重複。')
    hook = plan['hook']
    fit_text(hook['lead'], font(fonts, serif=True, size=88))
    fit_text(hook['question'], font(fonts, serif=True, size=96))
    if not isinstance(hook['end_part'], int) or not 1 <= hook['end_part'] <= len(parts):
        raise ValueError('Hook 結尾段落無效。')
    return plan, amap, audio, sources


def timestamp(seconds, ass=True):
    unit = 100 if ass else 1000
    ticks = math.floor(seconds * unit + 1e-6) if ass else round(seconds * unit)
    seconds, fraction = divmod(ticks, unit)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return (f'{hours}:{minutes:02}:{seconds:02}.{fraction:02}' if ass else
            f'{hours:02}:{minutes:02}:{seconds:02},{fraction:03}')


def subtitles(plan, amap, out):
    header = '''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,Source Han Sans TW,90,&H0000DCFF,&H0000DCFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    events, srt = [], []
    def event(a, b, text, tags, layer=1):
        events.append(f'Dialogue: {layer},{timestamp(a)},{timestamp(b)},Chinese,,0,0,0,,{{{tags}}}' + text.replace('\n', r'\N'))
    for i, (part, caption) in enumerate(zip(amap['parts'], plan['captions']), 1):
        event(part['start'], part['end'], caption, r'\pos(540,1410)', 2)
        srt.append(f"{i}\n{timestamp(part['start'], False)} --> {timestamp(part['end'], False)}\n{caption}")
    hook = plan['hook']
    end = amap['parts'][hook['end_part'] - 1]['end']
    event(0, end, hook['lead'], r'\fnSource Han Serif TC\fs88\pos(540,410)\1c&HFFFFFF&')
    event(0, end, hook['question'], r'\fnSource Han Serif TC\fs96\pos(540,650)\1c&H7077EF&')
    for scene in plan['scenes']:
        a = amap['parts'][scene['parts'][0] - 1]['start']
        b = amap['parts'][scene['parts'][-1] - 1]['end']
        event(a, b, scene['credit'], r'\an9\pos(995,115)\fs34\1c&HDDDDDD&\bord1')
        if a >= end and scene.get('title'):
            event(a, b, scene['title'], r'\fnSource Han Serif TC\fs96\pos(540,578)\1c&H7077EF&\fad(120,0)')
        if scene['kind'] == 'diagram':
            event(a, b, scene['body'], r'\fs58\pos(540,1190)\1c&HFFFFFF&')
    (out / 'captions.ass').write_text(header + '\n'.join(events) + '\n', encoding='utf-8')
    (out / 'captions.srt').write_text('\n\n'.join(srt) + '\n', encoding='utf-8')


def card(scene, fonts, path, index, count):
    im = Image.new('RGB', (WIDTH, HEIGHT), '#111d2b')
    draw = ImageDraw.Draw(im)
    for y in range(HEIGHT):
        light = int(10 * (1 - y / HEIGHT))
        draw.line((0, y, WIDTH, y), fill=(13 + light, 23 + light, 35 + light))
    draw.text((85, 200), 'MagicReels / FIELD NOTES', font=font(fonts, size=32), fill='#7893a5')
    draw.line((85, 280, 995, 280), fill='#3a5164', width=2)
    draw.text((85, 325), f'{index:02} / {count:02}', font=font(fonts, size=42), fill='#EF7770')
    lines = scene['body'].split('\n')
    for i, line in enumerate(lines):
        draw.text((540, 900 + i * 95), line, anchor='mm', font=font(fonts, size=58), fill='#eaf0f4')
    draw.line((90, 1620, 990, 1620), fill='#344556', width=3)
    draw.line((90, 1620, 90 + 900 * index / count, 1620), fill='#EF7770', width=6)
    draw.text((90, 1680), '長文 → 腳本 → 聲音 → 影像', font=font(fonts, size=34), fill='#7893a5')
    im.save(path)


def render(plan_file, fonts, output):
    plan_file, fonts = Path(plan_file).resolve(), Path(fonts).resolve()
    plan, amap, audio, sources = validate(plan_file, fonts)
    out = new_output(output)
    (out / 'fonts').mkdir()
    for name in ('SourceHanSansTW-Bold.otf', 'SourceHanSerifTC-Bold.otf'):
        shutil.copy2(fonts / name, out / 'fonts' / name)
    mask = np.zeros((HEIGHT, WIDTH, 4), dtype=np.uint8)
    mask[:, :, 3] = (125 + 34 * np.clip((np.arange(HEIGHT) - 1050) / (HEIGHT - 1050), 0, 1))[:, None].astype(np.uint8)
    Image.fromarray(mask).save(out / 'dark-overlay.png')
    subtitles(plan, amap, out)
    shots = []
    for i, scene in enumerate(plan['scenes'], 1):
        a = round(amap['parts'][scene['parts'][0] - 1]['start'] * FPS)
        b = round(amap['parts'][scene['parts'][-1] - 1]['end'] * FPS)
        if i == len(plan['scenes']):
            b = math.ceil(amap['duration'] * FPS)
        if b <= a:
            raise ValueError('分鏡長度不足一個影格。')
        kind = scene['kind']
        if kind == 'card':
            source = out / f'card-{i:03}.png'
            card(scene, fonts, source, i, len(plan['scenes']))
        else:
            source = checked_path(plan_file.parent, scene['path'])
        args = ['ffmpeg', '-v', 'error', '-n']
        args += (['-ss', str(scene.get('source_in', 0))] if kind == 'video' else ['-loop', '1', '-framerate', str(FPS)])
        args += ['-i', str(source)]
        vf = 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=0x111d2b,setsar=1,fps=30'
        if kind == 'video':
            vf = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30'
        elif kind == 'diagram':
            vf = 'scale=940:900:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:450:color=0x0C2643,setsar=1,fps=30'
        if kind == 'image':
            vf += ',drawbox=color=black@0.45:t=fill'
        filters = ['-vf', vf]
        if kind == 'video':
            # Alpha compositing preserves source color and darkens the subtitle zone.
            args += ['-loop', '1', '-i', str(out / 'dark-overlay.png')]
            filters = ['-filter_complex_threads', '2', '-filter_complex',
                       f'[0:v]{vf}[base];[base][1:v]overlay=0:0:shortest=1[v]', '-map', '[v]']
        name = f'shot-{i:03}.mp4'
        run(args + filters + ['-frames:v', str(b - a), '-an', '-c:v', 'libx264',
                    '-crf', '20', '-preset', 'fast', '-threads', '3', '-pix_fmt', 'yuv420p', str(out / name)])
        shots.append(name)
        print(f'分鏡 {i}/{len(plan["scenes"])}', flush=True)
    (out / 'concat.txt').write_text(''.join(f"file '{name}'\n" for name in shots))
    run(['ffmpeg', '-v', 'error', '-n', '-f', 'concat', '-safe', '1', '-i', 'concat.txt', '-c', 'copy', 'picture.mp4'], cwd=out)
    run(['ffmpeg', '-v', 'error', '-n', '-i', 'picture.mp4', '-i', str(audio), '-map', '0:v:0', '-map', '1:a:0',
         '-vf', 'ass=captions.ass:fontsdir=fonts', '-af', 'apad', '-t', str(math.ceil(amap['duration'] * FPS) / FPS),
         '-c:v', 'libx264', '-crf', '20', '-preset', 'fast', '-threads', '4', '-pix_fmt', 'yuv420p',
         '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', 'film.mp4'], cwd=out)
    save(out / 'source-manifest.json', sources)
    save(out / 'manifest.json', {'version': '0.2.0', 'title': plan['title'], 'video': 'film.mp4',
         'audio_sha256': digest(audio), 'source_count': len(sources), 'duplicate_sources': [],
         'plan_sha256': digest(plan_file), 'human_visual_review': 'pending'})
    verify(out / 'film.mp4', out / 'verification.json')
    preview(out / 'film.mp4', out / 'preview.jpg')
    return out / 'film.mp4'


def verify(video, report):
    info = probe(video)
    v = next(s for s in info['streams'] if s['codec_type'] == 'video')
    a = next(s for s in info['streams'] if s['codec_type'] == 'audio')
    run(['ffmpeg', '-v', 'error', '-i', str(video), '-f', 'null', '-'])
    tail = abs(float(v['duration']) - float(a['duration']))
    if (v['width'], v['height'], v['codec_name'], v['pix_fmt'], v['r_frame_rate']) != (WIDTH, HEIGHT, 'h264', 'yuv420p', '30/1') or a['codec_name'] != 'aac' or tail > 1 / FPS + .002:
        raise ValueError('輸出格式或聲畫尾差未通過。')
    loudness = subprocess.run(['ffmpeg', '-v', 'info', '-i', str(video), '-af',
        'loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, check=True)
    log = loudness.stderr.decode('utf-8', errors='replace')
    measured = json.loads(log[log.rfind('{'):log.rfind('}') + 1])
    true_peak = float(measured['input_tp'])
    if not math.isfinite(true_peak) or true_peak > 0:
        raise ValueError('成片音訊無有效真峰值，或真峰值超過 0 dBTP。')
    result = {'full_decode': 'pass', 'width': WIDTH, 'height': HEIGHT, 'fps': FPS,
              'duration': float(info['format']['duration']), 'av_tail_difference': tail,
              'integrated_lufs': float(measured['input_i']), 'true_peak_dbtp': true_peak,
              'sha256': digest(video), 'human_listening': 'pending', 'human_visual_review': 'pending'}
    save(report, result)
    return result


def preview(video, target):
    duration = float(probe(video)['format']['duration'])
    count = max(6, math.ceil(duration / 5) + 1)
    sheet = Image.new('RGB', (390 * 3, 694 * math.ceil(count / 3)), '#111d2b')
    for i in range(count):
        path = Path(target).with_name(f'.preview-{i}.png')
        run(['ffmpeg', '-v', 'error', '-n', '-ss', str(min(duration - .1, .1 + i * duration / (count - 1))),
             '-i', str(video), '-frames:v', '1', '-vf', 'scale=390:694', str(path)])
        with Image.open(path) as im:
            sheet.paste(im, (i % 3 * 390, i // 3 * 694))
        path.unlink()
    sheet.save(target)


def db(samples):
    return float(10 * np.log10(max(float(np.mean(samples * samples)), 1e-20)))


def decode(path):
    raw = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0', '-ar', str(SR), '-ac', '2', '-f', 'f32le', '-'])
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2).astype(np.float64)


def mix_samples(voice, music, gap=18):
    if len(voice) < SR or not np.isfinite(voice).all() or not np.isfinite(music).all():
        raise ValueError('音訊過短或含無效樣本。')
    if db(voice) < -60 or db(music) < -70:
        raise ValueError('人聲或配樂為靜音。')
    count = len(voice)
    if len(music) < count - SR // FPS:
        raise ValueError('配樂長度不足，請產生涵蓋全片的配樂。')
    music = np.pad(music[:count], ((0, max(0, count - len(music))), (0, 0)))
    nodes = np.arange(0, count, SR // 4)
    power = np.concatenate([[0.0], np.cumsum(np.mean(music * music, axis=1))])
    lo, hi = np.maximum(0, nodes - int(1.5 * SR)), np.minimum(count, nodes + int(1.5 * SR))
    local = 10 * np.log10(np.maximum((power[hi] - power[lo]) / (hi - lo), 1e-15))
    gains = np.minimum(db(voice) - gap - local, 0)
    gains = np.convolve(np.pad(gains, (4, 4), mode='edge'), np.ones(9) / 9, mode='valid')
    bed = music * np.interp(np.arange(count), nodes, 10 ** (gains / 20))[:, None]
    fade = min(round(.35 * SR), count // 2)
    tail = min(round(1.8 * SR), count // 2)
    bed[:fade] *= np.linspace(0, 1, fade)[:, None]
    bed[-tail:] *= np.linspace(1, 0, tail)[:, None]
    active = [i for i in range(0, count - SR + 1, SR // 4) if db(voice[i:i + SR]) > db(voice) - 15]
    margins = [db(voice[i:i + SR]) - db(bed[i:i + SR]) for i in active]
    correction = max(0, 12 - min(margins)) if margins else 0
    bed *= 10 ** (-correction / 20)
    limit = 10 ** (-1 / 20)
    if np.max(np.abs(voice)) >= limit:
        raise ValueError('原始人聲峰值過高，請先準備有足夠餘裕的音軌。')
    # Reduce only the score when the sum approaches the fixed headroom limit.
    ratios = np.divide(limit - np.sign(bed) * voice, np.abs(bed),
                       out=np.full_like(bed, np.inf), where=np.abs(bed) > 1e-12)
    headroom_gain = min(1.0, float(np.min(ratios)) * .99)
    bed *= headroom_gain
    mixed = voice + bed
    if np.max(np.abs(mixed)) >= limit:
        raise ValueError('混音峰值過高；請先降低配樂或重新準備人聲。')
    return mixed, bed, {'target_gap_db': gap, 'overall_gap_db': db(voice) - db(bed),
        'min_active_1s_gap_db': min(margins) + correction - 20 * math.log10(headroom_gain) if margins else None,
        'headroom_music_gain_db': 20 * math.log10(headroom_gain),
        'additional_music_reduction_db': correction, 'voice_gain_db': 0,
        'voice_component_residual': float(np.max(np.abs((mixed - bed) - voice))),
        'sample_peak_dbfs': float(20 * np.log10(np.max(np.abs(mixed)))),
        'human_listening': 'pending', 'music_looped': False}


def frame_hashes(path):
    raw = run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:v:0', '-f', 'framemd5', '-']).decode()
    return [line.split(',')[-1].strip() for line in raw.splitlines() if line and not line.startswith('#')]


def mix(video, music, output):
    video, music = Path(video).resolve(), Path(music).resolve()
    duration = float(probe(video)['format']['duration'])
    if not math.isfinite(duration) or not 1 <= duration <= 180:
        raise ValueError('v0.2 支援 1–180 秒影片。')
    if next(s for s in probe(video)['streams'] if s['codec_type'] == 'video')['codec_name'] != 'h264':
        raise ValueError('混音輸入須為 H.264 MP4。')
    voice, score = decode(video), decode(music)
    mixed, bed, settings = mix_samples(voice, score)
    out = new_output(output)
    for name, samples in (('mixed.wav', mixed), ('music-bed.wav', bed)):
        run(['ffmpeg', '-v', 'error', '-n', '-f', 'f64le', '-ar', str(SR), '-ac', '2', '-i', '-',
             '-c:a', 'pcm_s24le', str(out / name)], input=samples.astype('<f8').tobytes())
    final = out / 'final.mp4'
    run(['ffmpeg', '-v', 'error', '-n', '-i', str(video), '-i', str(out / 'mixed.wav'),
         '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
         '-t', probe(video)['format']['duration'], '-movflags', '+faststart', str(final)])
    if frame_hashes(video) != frame_hashes(final):
        raise ValueError('混音前後畫面像素不同。')
    settings.update(video_frames_preserved=True, source_video_sha256=digest(video), music_sha256=digest(music))
    save(out / 'mix-settings.json', settings)
    for name in ('captions.ass', 'captions.srt', 'source-manifest.json'):
        if (video.parent / name).is_file():
            shutil.copy2(video.parent / name, out / name)
    verify(final, out / 'verification.json')
    preview(final, out / 'preview.jpg')
    return final
