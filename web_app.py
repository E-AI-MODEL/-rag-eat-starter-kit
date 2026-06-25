#!/usr/bin/env python3
"""Small local web UI for the RAG EAT Starter Kit.

Run with:
    python3 -m streamlit run web_app.py

Uploaded files are written to the local knowledge/ folder in the current clone.
They are intentionally ignored by Git, so they do not get committed to the
original repository by accident.
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Iterable, List

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402

DEFAULT_GROUPS = ["public", "support"]
DEMO_DIR = ROOT / "examples" / "corpus"
KNOWLEDGE_DIR = Path(os.environ.get("RAGKIT_CORPUS", ROOT / "knowledge"))
EAT_PATH = Path(os.environ.get("RAGKIT_EAT", ROOT / "prompts" / "rag_assistant.eat"))

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n", re.DOTALL)
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def parse_groups(value: str | None) -> List[str]:
    if not value:
        return DEFAULT_GROUPS
    groups = [item.strip() for item in value.split(",") if item.strip()]
    return groups or DEFAULT_GROUPS


def safe_stem(name: str) -> str:
    stem = Path(name).stem.strip() or "document"
    stem = _SAFE_NAME_RE.sub("-", stem).strip(".-_")
    return stem or "document"


def unique_path(folder: Path, filename: str) -> Path:
    path = folder / filename
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for number in range(2, 1000):
        candidate = folder / f"{stem}-{number}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError("Could not create a unique filename for the upload.")


def markdown_with_frontmatter(filename: str, text: str, groups: Iterable[str]) -> str:
    if _FRONTMATTER_RE.match(text):
        return text

    stem = safe_stem(filename)
    title = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or stem
    today = date.today().isoformat()
    groups_text = ", ".join(groups)
    frontmatter = "\n".join(
        [
            "---",
            f"source_id: {stem}",
            f"title: {json.dumps(title)}",
            f"family: {stem}",
            "document_type: uploaded",
            'version: "1.0"',
            f"created_at: {json.dumps(today)}",
            f"updated_at: {json.dumps(today)}",
            "owner: local_user",
            f"allowed_groups: [{groups_text}]",
            f"canonical_url: local://{stem}",
            "---",
            "",
        ]
    )

    if not text.lstrip().startswith("#"):
        text = f"# {title}\n\n{text.strip()}\n"
    return frontmatter + text.strip() + "\n"


def save_uploads(uploaded_files, groups: List[str]) -> List[Path]:
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    saved: List[Path] = []
    for uploaded in uploaded_files:
        raw = uploaded.getvalue().decode("utf-8", errors="replace")
        stem = safe_stem(uploaded.name)
        path = unique_path(KNOWLEDGE_DIR, f"{stem}.md")
        path.write_text(markdown_with_frontmatter(uploaded.name, raw, groups), encoding="utf-8")
        saved.append(path)
    return saved


def markdown_files(folder: Path) -> List[Path]:
    if not folder.exists():
        return []
    return sorted(path for path in folder.glob("*.md") if path.is_file())


def build_assistant(corpus_dir: Path, groups: List[str]) -> Assistant:
    profile = load_eat(str(EAT_PATH))
    chunks = load_corpus(str(corpus_dir))
    index = HybridIndex(chunks)
    return Assistant(profile, index, groups)


def render_sources(corpus_dir: Path) -> None:
    files = markdown_files(corpus_dir)
    st.subheader("Sources")
    st.caption(f"Folder: `{corpus_dir}`")

    if not files:
        st.info("No Markdown files found yet.")
        return

    for path in files:
        with st.expander(path.name):
            text = path.read_text(encoding="utf-8", errors="replace")
            st.code(text[:4000], language="markdown")
            if len(text) > 4000:
                st.caption("Preview truncated after 4000 characters.")


def main() -> None:
    st.set_page_config(page_title="RAG EAT Starter Kit", page_icon="📄", layout="wide")
    st.title("RAG EAT Starter Kit")
    st.caption("A small local web interface on top of the existing starter kit.")

    groups = parse_groups(os.environ.get("RAGKIT_USER_GROUPS"))

    with st.sidebar:
        st.header("Menu")
        page = st.radio("Go to", ["Ask a question", "Sources", "How it works"])
        corpus_choice = st.radio(
            "Corpus",
            ["knowledge", "demo"],
            help="Use knowledge for your own documents and demo for the included sample data.",
        )
        corpus_dir = KNOWLEDGE_DIR if corpus_choice == "knowledge" else DEMO_DIR

        st.divider()
        st.subheader("Upload documents")
        st.caption("Uploads are saved locally in `knowledge/` and ignored by Git by default.")
        uploaded_files = st.file_uploader(
            "Upload Markdown or text",
            type=["md", "markdown", "txt"],
            accept_multiple_files=True,
        )
        if st.button("Save to knowledge/", disabled=not uploaded_files):
            saved = save_uploads(uploaded_files or [], groups)
            if saved:
                st.success("Saved: " + ", ".join(path.name for path in saved))
                st.rerun()

        st.divider()
        st.subheader("Access")
        st.caption("Current groups: " + ", ".join(groups))

    if page == "Ask a question":
        st.subheader("Ask a question")
        st.caption(f"Active source folder: `{corpus_dir}`")

        files = markdown_files(corpus_dir)
        if not files:
            st.warning("This source folder does not contain Markdown files yet.")

        question = st.text_input("Question", placeholder="For example: What are the cancellation conditions?")
        if st.button("Answer question", type="primary", disabled=not question.strip()):
            try:
                assistant = build_assistant(corpus_dir, groups)
                result = assistant.answer(question.strip())
            except Exception as exc:  # noqa: BLE001
                st.error(f"Could not process the question: {exc}")
                return

            st.markdown("### Answer")
            st.write(result.answer)

            if result.abstained:
                st.info(
                    "The assistant found no matching accessible source, so it refused to guess."
                )
            elif result.citations:
                st.markdown("### Sources used")
                for hit in result.citations:
                    st.write(f"- {hit.chunk.citation()} — score {hit.score:.3f}")

    elif page == "Sources":
        render_sources(corpus_dir)

    else:
        st.subheader("How it works")
        st.markdown(
            """
1. Put your own Markdown or text files in `knowledge/`, or upload them with the button on the left.
2. Ask a question.
3. The app retrieves matching passages first.
4. Only accessible sources can be used in the answer.
5. If there is no matching source, the assistant says it cannot answer reliably from the retrieved sources.

Uploads are saved in the environment where the app runs. If someone uses a fork,
local clone or Codespace, the files stay there. They are not added to the original repository automatically.
"""
        )


if __name__ == "__main__":
    main()
