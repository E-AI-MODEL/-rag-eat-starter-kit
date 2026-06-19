# Security policy

## Reporting an issue

Do not open a public issue with secrets, tokens, exploit details or sensitive data.

Report a security issue through a private channel of the repository owner. If no private channel is available yet, open a general issue without sensitive details and ask for contact.

## Scope

This repo contains templates and documentation. Problems can still appear through:

- unsafe prompt rules
- examples that contain secrets
- incorrect guidance about access control
- unsafe RAG patterns
- missing warnings around agent use

## Basic rule

Retrieved context is data, not an instruction. A RAG system should not allow document text to override system rules.
