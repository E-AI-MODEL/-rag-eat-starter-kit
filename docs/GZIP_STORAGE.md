# Gzip storage boundary

The repository has one explicit compressed-data area:

```text
datasets/compressed/
```

Everything below this directory must be a valid `.gz` file. The only exception is a local `README.md` that explains the directory. CI validates this rule.

## What belongs there

Use the boundary for large, stable, text-based data such as:

- `.json` and `.jsonl` datasets
- `.csv` exports
- large Markdown or plain-text corpora
- YAML snapshots

Keep source code, active prompts, configuration, documentation and frequently edited examples outside the boundary. Git cannot produce useful line diffs for gzip files.

## Transparent corpus loading

`load_corpus()` now discovers documents recursively and accepts:

- `.md`
- `.markdown`
- `.md.gz`
- `.markdown.gz`

A compressed document is decompressed in memory and parsed exactly like a plain Markdown document. Front matter, access groups, sections and source IDs keep working.

Do not keep both `policy.md` and `policy.md.gz` under the same corpus root. The loader rejects that ambiguous pair instead of indexing the document twice.

## Commands

Install the package, then validate the boundary:

```bash
rag-eat-gzip check
```

Compress one file:

```bash
rag-eat-gzip compress data/records.jsonl datasets/compressed/records.jsonl.gz
```

Move the source into compressed storage after a successful write:

```bash
rag-eat-gzip compress data/records.jsonl datasets/compressed/records.jsonl.gz --remove-source
```

Compress all eligible files of at least 256 KiB from a tree:

```bash
rag-eat-gzip compress-tree data/raw
```

Choose another threshold in bytes:

```bash
rag-eat-gzip compress-tree data/raw --threshold 1048576
```

Preserve the original files by default. Add `--remove-source` only after checking the output and updating references.

## Reproducible output

The compressor writes gzip files with timestamp `0` and without embedding the source filename. The same input produces the same bytes. This avoids meaningless Git changes caused by timestamps or local paths.

## CI contract

CI runs:

```bash
rag-eat-gzip check
```

A change fails when:

- an uncompressed data file appears below `datasets/compressed/`
- a `.gz` file is corrupt or incomplete
- tests for compressed corpus loading fail

## Limits

Gzip reduces repository, transfer and storage size. It does not reduce the number of tokens after decompression. LLM providers receive normal text unless their HTTP client and server explicitly support compressed request bodies.