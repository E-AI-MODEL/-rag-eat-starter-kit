# Beginner start

This page is for people who want to try the RAG starter kit without typing many terminal commands.

## Start the web app

From the repository root:

```bash
bash start.sh
```

The script creates a local Python environment, installs the small set of dependencies, validates the EAT profile, and starts the web app.

## Add your own documents

Open the web app and use the upload button in the sidebar.

Supported file types:

- `.md`
- `.markdown`
- `.txt`

Uploaded files are saved in `knowledge/` in the environment where the app runs.

## What happens to uploaded documents?

They are local by default.

If someone runs this from their own fork, local clone or Codespace, uploaded files are saved there. They do not appear in the original `E-AI-MODEL/-rag-eat-starter-kit` repository.

The `.gitignore` file also ignores uploaded Markdown files in `knowledge/`, except the included `README.md` and `example.md`. This helps prevent private test documents from being committed by accident.

## Use the demo documents instead

In the sidebar, change `Corpus` from `knowledge` to `demo`.

The demo corpus is still in:

```text
examples/corpus/
```

The beginner web app does not remove or replace the original demo.

## Ask a first question

With `Corpus` set to `knowledge`, ask:

```text
What does this starter kit do?
```

With `Corpus` set to `demo`, ask:

```text
What are the cancellation conditions?
```

## Advanced: choose groups

The default user groups are:

```text
public,support
```

You can override them before starting the app:

```bash
RAGKIT_USER_GROUPS="public,support,finance" bash start.sh
```

Only documents with a matching `allowed_groups` value can be retrieved.
