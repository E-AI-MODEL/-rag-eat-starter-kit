#!/usr/bin/env python3
"""Small local web UI for the RAG EAT Starter Kit.

Run with:
    python3 -m streamlit run web_app.py

Uploaded files are written to the local knowledge/ folder in the current clone.
They are intentionally ignored by Git, so they do not get committed to the
original repository by accident.
"""

from __future__ import annotations

import os
import re
import sys
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from ragkit import HybridIndex, load_corpus, load_eat  # noqa: E402
from ragkit.assistant import Assistant  # noqa: E402

DEFAULT_GROUPS = ["public", "support"]
DEMO_DIR = ROOT / "examples" / "corpus"
KNOWLEDGE_DIR = Path(os.environ.get("RAGKIT_CORPUS", ROOT / "knowledge"))
EAT_PATH = Path(os.environ.get("RAGKIT_EAT", ROOT / "prompts" / "rag_assistant.eat"))

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9._-]+")
_GROUP_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")

EXAMPLE_QUESTIONS = {
    "knowledge": [
        "What does this starter kit do?",
        "How should the assistant behave when the answer is missing?",
    ],
    "demo": [
        "What are the cancellation conditions?",
        "What does product code X-123 mean?",
        "What is the internal pricing markup?",
    ],
}


def normalize_groups(groups: Iterable[str]) -> List[str]:
    """Return validated group names for access filtering."""
    clean: List[str] = []
    seen = set()
    for raw in groups:
        group = raw.strip()
        if not group:
            continue
        if not _GROUP_RE.match(group):
            raise ValueError(
                "Group names may only contain letters, numbers, dots, underscores "
                f"and hyphens: {group!r}"
            )
        if group not in seen:
            clean.append(group)
            seen.add(group)
    return clean or list(DEFAULT_GROUPS)


def parse_groups(value: Optional[str]) -> List[str]:
    if not value:
        return list(DEFAULT_GROUPS)
    return normalize_groups(value.split(","))


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

    valid_groups = normalize_groups(groups)
    stem = safe_stem(filename)
    title = Path(filename).stem.replace("_", " ").replace("-", " ").strip() or stem
    today = date.today().isoformat()
    metadata = {
        "source_id": stem,
        "title": title,
        "family": stem,
        "document_type": "uploaded",
        "version": "1.0",
        "created_at": today,
        "updated_at": today,
        "owner": "local_user",
        "allowed_groups": valid_groups,
        "canonical_url": f"local://{stem}",
    }
    yaml_text = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).strip()
    frontmatter = f"---\n{yaml_text}\n---\n\n"

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
        content = markdown_with_frontmatter(path.name, raw, groups)
        path.write_text(content, encoding="utf-8")
        saved.append(path)
    return saved


def markdown_files(folder: Path) -> List[Path]:
    if not folder.exists():
        return []
    return sorted(path for path in folder.glob("*.md") if path.is_file())


def read_document(path: Path) -> Tuple[Dict[str, object], str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text

    try:
        metadata = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        metadata = {}

    if not isinstance(metadata, dict):
        metadata = {}
    body = text[match.end() :].lstrip("\n")
    return metadata, body


def corpus_stats(corpus_dir: Path) -> Tuple[int, int, Optional[str]]:
    files = markdown_files(corpus_dir)
    if not files:
        return 0, 0, None

    try:
        chunks = load_corpus(str(corpus_dir))
    except Exception as exc:  # noqa: BLE001
        return len(files), 0, str(exc)
    return len(files), len(chunks), None


def build_assistant(corpus_dir: Path, groups: List[str]) -> Assistant:
    profile = load_eat(str(EAT_PATH))
    chunks = load_corpus(str(corpus_dir))
    index = HybridIndex(chunks)
    return Assistant(profile, index, groups)


def render_status(corpus_name: str, corpus_dir: Path, groups: List[str]) -> None:
    file_count, chunk_count, error = corpus_stats(corpus_dir)
    cols = st.columns(4)
    cols[0].metric("Corpus", corpus_name)
    cols[1].metric("Documents", file_count)
    cols[2].metric("Chunks", chunk_count)
    cols[3].metric("Groups", len(groups))

    if error:
        st.warning(f"Could not load this corpus: {error}")


def render_upload(saved_key: str, groups: List[str]) -> None:
    st.subheader("Upload documents")
    st.caption(
        "Supported: `.md`, `.markdown` and `.txt`. Files are saved locally in "
        "`knowledge/` and ignored by Git by default."
    )
    uploaded_files = st.file_uploader(
        "Choose files",
        type=["md", "markdown", "txt"],
        accept_multiple_files=True,
    )

    if st.button("Save to knowledge/", disabled=not uploaded_files):
        saved = save_uploads(uploaded_files or [], groups)
        st.session_state[saved_key] = [path.name for path in saved]
        if saved:
            st.rerun()

    saved_names = st.session_state.get(saved_key, [])
    if saved_names:
        st.success("Saved: " + ", ".join(saved_names))


def render_source_cards(corpus_dir: Path) -> None:
    files = markdown_files(corpus_dir)
    st.subheader("Sources")
    st.caption(f"Folder: `{corpus_dir}`")

    if not files:
        st.info("No Markdown files found yet. Upload a file or use the demo corpus.")
        return

    for path in files:
        metadata, body = read_document(path)
        title = str(metadata.get("title") or path.stem)
        source_id = str(metadata.get("source_id") or path.stem)
        groups = metadata.get("allowed_groups") or []
        updated = metadata.get("updated_at") or "n/a"

        with st.expander(f"{title} ({path.name})"):
            cols = st.columns(3)
            cols[0].caption(f"Source ID: `{source_id}`")
            cols[1].caption(f"Updated: `{updated}`")
            cols[2].caption(f"Groups: `{groups}`")
            st.code(body[:4000], language="markdown")
            if len(body) > 4000:
                st.caption("Preview truncated after 4000 characters.")


def set_example_question(question: str) -> None:
    st.session_state.question = question


def render_question_page(corpus_name: str, corpus_dir: Path, groups: List[str]) -> None:
    st.subheader("Ask a question")
    st.caption(f"Active source folder: `{corpus_dir}`")

    file_count, _, error = corpus_stats(corpus_dir)
    if file_count == 0:
        st.info("Start by uploading a document, or switch to the demo corpus in the sidebar.")
    if error:
        st.stop()

    examples = EXAMPLE_QUESTIONS.get(corpus_name, [])
    if examples:
        st.markdown("Try an example question:")
        cols = st.columns(len(examples))
        for index, question in enumerate(examples):
            cols[index].button(
                question,
                key=f"example_{corpus_name}_{index}",
                on_click=set_example_question,
                args=(question,),
            )

    if "question" not in st.session_state:
        st.session_state.question = examples[0] if examples else ""

    question = st.text_input("Question", key="question")
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
            st.info("No matching accessible source was found, so the assistant did not guess.")
        elif result.citations:
            st.markdown("### Sources used")
            for hit in result.citations:
                st.write(f"- {hit.chunk.citation()} - score {hit.score:.3f}")


def render_how_it_works() -> None:
    st.subheader("How it works")
    st.markdown(
        """
1. Add Markdown or text files to `knowledge/`, or upload them with the sidebar.
2. Ask a question.
3. The app retrieves matching passages first.
4. Access control is applied before answering.
5. If there is no matching accessible source, the assistant refuses to guess.
"""
    )

    st.subheader("Where does this website run?")
    st.markdown(
        """
This is a local Streamlit app. When you run `bash start.sh`, the web server starts in
that terminal session and opens in your browser, normally at `http://localhost:8501`.

If someone runs it in their own fork, local clone or Codespace, uploads stay in that
environment. They are not sent to the original repository automatically.

It is not a public website unless you deploy it yourself on a server or hosting platform.
"""
    )


def main() -> None:
    st.set_page_config(page_title="RAG EAT Starter Kit", page_icon="📄", layout="wide")
    st.title("RAG EAT Starter Kit")
    st.caption("A local beginner web interface for grounded document Q&A.")

    with st.sidebar:
        st.header("Menu")
        page = st.radio("Go to", ["Ask", "Sources", "How it works"])
        corpus_name = st.radio(
            "Corpus",
            ["knowledge", "demo"],
            help="Use knowledge for your own documents and demo for the sample data.",
        )
        corpus_dir = KNOWLEDGE_DIR if corpus_name == "knowledge" else DEMO_DIR

        st.divider()
        group_text = st.text_input(
            "Current user groups",
            value=os.environ.get("RAGKIT_USER_GROUPS", "public,support"),
            help="Comma-separated groups used for access filtering.",
        )
        try:
            groups = parse_groups(group_text)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()
        st.caption("Active groups: " + ", ".join(groups))

        st.divider()
        render_upload("saved_uploads", groups)

    render_status(corpus_name, corpus_dir, groups)
    st.divider()

    if page == "Ask":
        render_question_page(corpus_name, corpus_dir, groups)
    elif page == "Sources":
        render_source_cards(corpus_dir)
    else:
        render_how_it_works()


if __name__ == "__main__":
    main()
