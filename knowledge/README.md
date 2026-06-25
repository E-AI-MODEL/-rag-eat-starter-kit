# Knowledge folder

Put your own Markdown files here when you want to try the starter kit with your own content.

The web app also saves uploaded `.md`, `.markdown` and `.txt` files in this folder.
Those uploaded files are ignored by Git by default, so private test documents do not get committed to this repository by accident.

## What happens in a fork?

If someone forks this repository, their uploaded documents are saved in their own fork, clone or Codespace. They do not change the original `E-AI-MODEL/-rag-eat-starter-kit` repository.

If they want to share changes back, they must make a pull request. You decide whether to merge it.

## Minimal document format

A document can be plain text. The web app will add metadata automatically when you upload it.

For hand-written Markdown, this format gives you full control:

```markdown
---
source_id: example_policy
title: Example Policy
family: example_policy
document_type: policy
version: "1.0"
created_at: "2026-06-26"
updated_at: "2026-06-26"
owner: local_user
allowed_groups: [public, support]
canonical_url: local://example_policy
---

# Main rule

Write the information that the assistant may use here.
```

A document without matching `allowed_groups` is not retrieved.
