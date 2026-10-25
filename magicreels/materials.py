"""Pexels candidate search; source identity and editorial review stay explicit."""
import json
import os
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

from .pipeline import new_output, save, run, digest


def api(path, params=None):
    key = os.environ.get('PEXELS_API_KEY', '').strip()
    if not key:
        raise ValueError('請設定 PEXELS_API_KEY。')
    url = 'https://api.pexels.com' + path
    if params:
        url += '?' + urlencode(params)
    with urlopen(Request(url, headers={'Authorization': key, 'User-Agent': 'MagicReels/0.2'}), timeout=30) as response:
        return json.load(response)


def row(video):
    return {'source_asset_id': f"pexels:video:{video['id']}", 'video_id': video['id'],
            'source_page': video['url'], 'creator': video['user']['name'],
            'duration': video['duration'], 'width': video['width'], 'height': video['height'],
            'license_page': 'https://www.pexels.com/license/', 'reviewed': False}


def search(query, output):
    results = api('/v1/videos/search', {'query': query, 'orientation': 'portrait', 'per_page': 12})
    out = new_output(output)
    save(out / 'candidates.json', {'query': query, 'candidates': [row(v) for v in results.get('videos', [])]})
    return out / 'candidates.json'


def fetch(video_id, output):
    if not isinstance(video_id, int) or video_id < 1:
        raise ValueError('素材 ID 須為正整數。')
    video = api(f'/v1/videos/videos/{video_id}')
    versions = [v for v in video['video_files'] if v.get('file_type') == 'video/mp4'
                and v.get('width') and v.get('height') and max(v['width'], v['height']) <= 1920]
    if not versions:
        raise ValueError('找不到合適的 MP4 版本。')
    selected = max(versions, key=lambda v: v['width'] * v['height'])
    url = urlsplit(selected['link'])
    if url.scheme != 'https' or not (url.hostname or '').endswith('.pexels.com') or url.username or url.password:
        raise ValueError('下載網址不在 Pexels HTTPS 來源內。')
    out = new_output(output)
    partial, target = out / 'video.part', out / 'video.mp4'
    request = Request(selected['link'], headers={'User-Agent': 'Mozilla/5.0 (compatible; MagicReels/0.2)',
                                                'Referer': 'https://www.pexels.com/'})
    with urlopen(request, timeout=90) as response, partial.open('xb') as stream:
        total = 0
        while block := response.read(1024 * 1024):
            total += len(block)
            if total > 250 * 1024 * 1024:
                raise ValueError('素材超過 250 MB，請選其他版本。')
            stream.write(block)
    run(['ffmpeg', '-v', 'error', '-i', str(partial), '-f', 'null', '-'])
    partial.rename(target)
    for i, fraction in enumerate((.15, .5, .8), 1):
        run(['ffmpeg', '-v', 'error', '-n', '-ss', str(video['duration'] * fraction), '-i', str(target),
             '-frames:v', '1', '-vf', 'scale=390:-2', str(out / f'review-{i}.jpg')])
    record = row(video)
    record.update(path='video.mp4', credit=f"示意畫面／Pexels · {video['user']['name']}",
                  sha256=digest(target), rendition={k: selected.get(k) for k in ('id', 'width', 'height')})
    save(out / 'source.json', record)
    return target
