# Human30 local CPU paired-run evidence

The four axis folders contain generated prompts, unedited UTF-8 model responses,
two independent repeats per baseline and condition arm, run receipts, and
manifests. The runs were produced with
`scripts/run_local_human30_pairs.py` using the pinned SmolLM2 revision, CPU,
PyTorch seed 42 applied before each generation, and the sampling settings in
each manifest. Each condition changes exactly its named axis. The verifier
compares repeated responses as bytes and checks model, prompt, runner, and
response hashes. This evidence concerns a fictional shelter scene; it does
not establish provider reproducibility, personal prediction, or causal effect.

The 257 MiB `model.safetensors` weight is excluded from Git. To acquire the
exact model files at the recorded immutable revision, run:

```sh
uv run --group dev python scripts/acquire_human30_model.py
uv run --group dev python scripts/verify_human30_repro.py
```

The acquisition script verifies every file against the SHA-256 values in the
manifests before using it. The weight pin is
`5af571cbf074e6d21a03528d2330792e532ca608f24ac70a143f6b369968ab8c`.
Existing local files are checked the same way. The runner requires PyTorch
2.10.0, Transformers 4.51.3, and safetensors 0.5.3 for regeneration; the
verification command only uses the project's existing dev dependencies.

From the repository root, regenerate all four axes in an isolated Python 3.10
environment, refresh the verdict hashes, and verify the result:

```sh
uv run --no-project --python 3.10 --with torch==2.10.0 --with transformers==4.51.3 --with safetensors==0.5.3 python -m scripts.run_local_human30_pairs --axes body memory identity world_model
uv run --group dev python scripts/build_human30_report.py
uv run --group dev python scripts/verify_human30_repro.py
uv run --group dev python scripts/verify_human30_report.py
uv run --group dev python -m pytest -q
```

The `revision` in each manifest is the model repository's immutable 40-character
commit ID. The acquisition command checks the six files at that commit against
their manifest SHA-256 hashes. Regeneration can change the receipt's invocation
path, so refresh the verdict hashes before running its verifier. These checks
establish reproducibility for this local CPU setup; they do not establish
provider seed application or an effect on real people.
