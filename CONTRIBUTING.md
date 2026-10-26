# Contributing

Start with a small, reproducible issue or a narrowly scoped pull request. Keep the v0.3 contract: one local production workflow, explicit review steps, portable paths and versioned output directories.

Run `python -m unittest discover -s tests -v`. Changes to rendering should include a decoded output check and a 390 px preview. Changes to timing or mixing should verify speech preservation and audio/video duration. Keep upstream licenses when importing code or assets.

Do not attach API credentials, private reference voices, unpublished articles or footage without redistribution rights. Use the bundled example or an original minimal fixture.

Support is best effort. Discuss large features before implementation.
