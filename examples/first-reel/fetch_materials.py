"""Download the six example sources locally; retain Pexels source records."""
from pathlib import Path
import argparse
import re
from magicreels.materials import fetch
from magicreels.pipeline import digest, load


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-only', action='store_true', help='Check committed source records without network access')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    items = load(root / 'materials.json')['videos']
    plan = load(root / 'project.json')
    ids = {f"pexels:video:{item['video_id']}" for item in items}
    assert len(ids) == len(items), 'Repeated source IDs in the material list'
    assert ids == {s['source_asset_id'] for s in plan['scenes'] if s['kind'] == 'video'}
    audio_map = load(root / plan['audio_map'])
    assert digest(root / 'voice' / audio_map['master']) == audio_map['master_sha256']
    for image in load(root / 'visual-prompts.json')['assets']:
        assert digest(root / image['file']) == image['sha256']
    for item in items:
        assert type(item['video_id']) is int and item['video_id'] > 0
        assert re.fullmatch(r'[0-9a-f]{64}', item['sha256'])
        assert item['source_page'].startswith('https://www.pexels.com/') and item['creator']
    if args.check_only:
        print('Example source records and narration hash: verified')
        return
    for item in items:
        target = root / 'assets/pexels' / str(item['video_id'])
        path = target / 'video.mp4'
        if not path.is_file():
            fetch(item['video_id'], target)
        if digest(path) != item['sha256']:
            raise ValueError(f"來源內容已改變，請重新核對：Pexels {item['video_id']}")
        print(f"Pexels {item['video_id']}: verified", flush=True)


if __name__ == '__main__':
    main()
