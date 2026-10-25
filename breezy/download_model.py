"""Download a pinned model and verify upstream SHA-256 records."""
import hashlib
import json
import os
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
os.environ['HF_HOME'] = str(root / 'cache/huggingface')
os.environ['HF_XET_CACHE'] = str(root / 'cache/huggingface/xet')
from huggingface_hub import snapshot_download

manifest = json.loads((Path(__file__).parent / 'model-manifest.json').read_text())
target = root / 'models/BreezyVoice'
snapshot_download(manifest['repository'], revision=manifest['revision'], local_dir=str(target),
                  cache_dir=str(root / 'cache/huggingface'))
for item in manifest['files']:
    if 'lfs' not in item:
        continue
    path = target / item['rfilename']
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    if path.stat().st_size != item['lfs']['size'] or h.hexdigest() != item['lfs']['sha256']:
        raise ValueError(f'Model integrity check failed: {item["rfilename"]}')
print('Pinned model hashes: pass')
