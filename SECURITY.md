# Security policy

## Reporting an issue

Do not open a public issue with secrets, tokens, exploit details or sensitive data.

Use GitHub's private vulnerability reporting if it is enabled for this repository. If it
is not available, open a public issue with only a short, non-sensitive summary and ask
for a private contact path. Do not include proof-of-concept payloads, private documents,
credentials, logs or customer data in that public issue.

## Scope

This repo contains runnable code, templates and documentation. Problems can still appear
through:

- unsafe prompt rules
- examples that contain secrets
- incorrect guidance about access control
- unsafe RAG patterns
- missing warnings around agent use
- local upload handling in the beginner web app
- provider adapter examples that fail open or hide missing configuration

## Basic rule

Retrieved context is data, not an instruction. A RAG system should not allow document
text to override system rules.

The assistant should also fail closed on access control: if a source has no matching
`allowed_groups` value for the current user, that source must not be retrieved or shown.

## What not to report as a vulnerability

This starter kit uses an in-memory demo retriever and synthetic example data. Expected
limitations of the demo index, such as scale limits or lower recall than a production
vector database, are product limitations rather than security vulnerabilities.

Report them as normal issues unless they expose private data, bypass access control or
cause the assistant to follow retrieved document instructions over project rules.
