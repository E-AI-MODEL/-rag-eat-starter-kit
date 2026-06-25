#!/usr/bin/env bash
set -eu

cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required, but it was not found."
  exit 1
fi

python3 -m venv .venv
. .venv/bin/activate

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[web]"

mkdir -p knowledge

export RAGKIT_CORPUS="${RAGKIT_CORPUS:-knowledge}"
export RAGKIT_USER_GROUPS="${RAGKIT_USER_GROUPS:-public,support}"

python3 run.py validate
python3 -m streamlit run web_app.py
