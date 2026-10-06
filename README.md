<p align="center"><img src="logo/citefilter_logo.svg" alt="CiteFilter" width="520"></p>

# CiteFilter

Give it the draft of an article (research or review) and your Zotero library. For every section
of the draft it suggests which of your papers fit, which figures from them could illustrate it,
and who to ask for permission to reuse a figure.

These are suggestions, not verdicts: nothing is removed, weaker matches are only listed lower.

## What it does

- **Papers per section** with a match %, after reading each paper's abstract and introduction.
- **Cited or not:** marks papers your draft already cites, and those that fit a section but are not cited yet.
- **Figures:** finds figure captions in the PDFs, suggests the best ones per section, and crops them out of the page.
- **Permission help:** corresponding author and licence from OpenAlex, email address from the PDF, and a draft permission email. It never sends anything.
- **Zotero:** reads a running Zotero 7 directly, or a CSV export.
- **Optional local model:** SPECTER2 matches by meaning, on your own computer.
- **Optional AI:** any OpenAI-style endpoint (a cloud provider or a local Ollama) can rate papers and personalise the emails.

Output is an HTML report plus a `papers.csv` table.

## Status

Early and lightly tested. Please read before relying on it.

- Developed and tested on one Mac (Apple Silicon) with a small test library.
- The Zotero connection and AI mode have only been tested against stand-in servers, not yet against a real Zotero or a real model.
- The Windows scripts have not been run on Windows yet. See [README_WINDOWS.md](README_WINDOWS.md).
- Matching is text similarity. A high % is not proof of relevance; a low % is not proof of irrelevance.
- Email addresses and licences are best guesses. Check them before use. For most journal papers the publisher, not the author, grants reuse permission.

## Run it

### Windows

Download `CiteFilter-for-Windows.zip` from this repository and follow [README_WINDOWS.md](README_WINDOWS.md).

### macOS / Linux, from source

Needs Python 3.10+ and Poppler (`brew install poppler` or `apt install poppler-utils`).

```bash
pip install -r requirements.txt
python3 citefilter_ui.py
```

Command line instead of the window:

```bash
python3 zotero_filter.py draft.docx library.csv
python3 zotero_filter.py draft.docx zotero            # read from a running Zotero 7
python3 zotero_filter.py draft.docx library.csv --semantic
```

For the local model also run `pip install torch adapters` (about 0.9 GB of model files are fetched on first use).
`python3 zotero_filter.py` with no arguments runs the built-in self-check.

To let CiteFilter read Zotero directly: Zotero > Settings > Advanced > tick
"Allow other applications on this computer to communicate with Zotero".

## What leaves your computer

| When | What is sent | Where |
|---|---|---|
| Always | DOIs of the suggested papers | OpenAlex |
| Local model, first use only | A model download request | Hugging Face |
| AI mode, only if you set an endpoint | Excerpts of your draft, abstracts, starts of introductions, figure captions | The endpoint you chose |

Without AI mode, your draft text never leaves your computer.

## Built with

Python, scikit-learn, python-docx, Tkinter, [Poppler](https://poppler.freedesktop.org/) (run as a separate
program), [OpenAlex](https://openalex.org/), and optionally [SPECTER2](https://huggingface.co/allenai/specter2)
through `transformers` and `adapters`.

## Licence

No licence has been chosen yet, so the usual copyright rules apply until one is added.
