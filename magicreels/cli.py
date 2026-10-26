"""Command-line workflow for MagicReels."""
import argparse
from pathlib import Path
from datetime import datetime, timezone

from . import __version__
from .pipeline import load, save, digest, checked_path, validate, render, mix, verify, new_output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', action='version', version=f'MagicReels {__version__}')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('validate', 'render'):
        p = commands.add_parser(name)
        p.add_argument('plan', type=Path)
        p.add_argument('--fonts', type=Path, default=Path('fonts'))
        if name == 'render':
            p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('mix')
    p.add_argument('video', type=Path)
    p.add_argument('--music', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('approve-audio', help='Record a human listening decision for this exact audio')
    p.add_argument('audio_map', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('verify')
    p.add_argument('video', type=Path)
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('search')
    p.add_argument('query')
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('fetch')
    p.add_argument('video_id', type=int)
    p.add_argument('--out', type=Path, required=True)
    p = commands.add_parser('transcribe', help='Whisper word timestamps for human alignment review')
    p.add_argument('audio', type=Path)
    p.add_argument('--model', default='small')
    p.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'validate':
            validate(args.plan, args.fonts)
            print('格式、字幕、旁白版本與素材唯一性：通過')
        elif args.command == 'render':
            print(render(args.plan, args.fonts, args.out))
        elif args.command == 'mix':
            print(mix(args.video, args.music, args.out))
        elif args.command == 'verify':
            if args.out.exists():
                raise FileExistsError(args.out)
            print(verify(args.video, args.out))
        elif args.command == 'approve-audio':
            record = load(args.audio_map)
            audio = checked_path(args.audio_map.resolve().parent, record['master'])
            if digest(audio) != record['master_sha256']:
                raise ValueError('音檔已改變，請重新建立音訊清單。')
            with args.out.open('x', encoding='utf-8') as stream:
                import json
                json.dump({'human_audition': 'approved', 'audio_sha256': digest(audio),
                           'recorded_at': datetime.now(timezone.utc).isoformat()}, stream, indent=2)
            print(args.out)
        elif args.command in ('search', 'fetch'):
            from . import materials
            print(materials.search(args.query, args.out) if args.command == 'search' else materials.fetch(args.video_id, args.out))
        elif args.command == 'transcribe':
            from faster_whisper import WhisperModel
            out = new_output(args.out)
            model = WhisperModel(args.model, device='cpu', compute_type='int8')
            segments, _ = model.transcribe(str(args.audio), language='zh', word_timestamps=True)
            save(out / 'whisper.json', {'audio_sha256': digest(args.audio), 'model': args.model,
                 'status': 'pending_human_review', 'segments': [
                     {'start': s.start, 'end': s.end, 'text': s.text,
                      'words': [{'start': w.start, 'end': w.end, 'word': w.word} for w in (s.words or [])]}
                     for s in segments]})
            print(out / 'whisper.json')
    except (ValueError, OSError, KeyError, RuntimeError) as error:
        parser.exit(2, f'錯誤：{error}\n')


if __name__ == '__main__':
    main()
