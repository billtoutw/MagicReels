#!/bin/sh
set -eu
BREEZY_SPEC=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BREEZY_TARGET=${1:-.runtime/breezy}
mkdir -p "$(dirname -- "$BREEZY_TARGET")"
mkdir "$BREEZY_TARGET"
BREEZY_TARGET=$(CDPATH= cd -- "$BREEZY_TARGET" && pwd)
command -v conda >/dev/null
command -v uv >/dev/null
command -v ffmpeg >/dev/null
# This tested environment targets Apple Silicon; Linux uses the upstream setup.
[ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = arm64 ] || { echo 'This setup requires macOS arm64. See docs/breezyvoice.md.' >&2; exit 1; }
git clone https://github.com/mtkresearch/BreezyVoice.git "$BREEZY_TARGET/upstream"
git -C "$BREEZY_TARGET/upstream" checkout d592c9d3e8927a0f53f68616387060dcd32a05ea
git -C "$BREEZY_TARGET/upstream" apply "$BREEZY_SPEC/macos-normalization.patch"
CONDA_REGISTER_ENVS=false CONDA_NUMBER_CHANNEL_NOTICES=0 CONDA_PKGS_DIRS="$BREEZY_TARGET/cache/conda" \
  conda create --prefix "$BREEZY_TARGET/env" --override-channels -c conda-forge \
  --no-default-packages python=3.10 pynini=2.1.5 pip --yes
uv --cache-dir "$BREEZY_TARGET/cache/uv" pip install --python "$BREEZY_TARGET/env/bin/python" \
  --build-constraint "$BREEZY_SPEC/build-constraints.txt" -r "$BREEZY_SPEC/requirements-lock.txt"
"$BREEZY_TARGET/env/bin/python" "$BREEZY_SPEC/download_model.py" "$BREEZY_TARGET"
cp "$BREEZY_SPEC/check_normalization.py" "$BREEZY_TARGET/check_normalization.py"
"$BREEZY_TARGET/env/bin/python" "$BREEZY_TARGET/check_normalization.py"
printf '%s\n' "BreezyVoice ready: $BREEZY_TARGET"
