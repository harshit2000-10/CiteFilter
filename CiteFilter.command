#!/bin/zsh
# Double-click to open the CiteFilter window.
cd "$(dirname "$0")" || exit 1
PY=/opt/miniconda3/bin/python3   # the Python that has scikit-learn, python-docx and Tk
[ -x "$PY" ] || PY=python3
exec "$PY" citefilter_ui.py
