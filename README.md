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

## Install

### Windows (installer)

1. Open the [Releases page](https://github.com/harshit2000-10/CiteFilter/releases) and download
   `CiteFilter-Setup-lite.exe` (small) or `CiteFilter-Setup-full.exe` (much larger, adds the optional local model).
2. Run it. Windows shows a SmartScreen warning because the installer is not code-signed:
   click **More info**, then **Run anyway**.
3. Start **CiteFilter** from the Start menu.

If no release is listed yet, build one: see [Build the installer yourself](#build-the-installer-yourself).

### Windows (from source)

Needs Windows 10/11 (64-bit) and Python 3.10+ from [python.org](https://www.python.org/downloads/windows/)
with **Add python.exe to PATH** ticked.

1. Download this repository (Code > Download ZIP) and unzip it, for example to `C:\CiteFilter`.
2. Double-click `setup_windows.bat` (about 10 minutes, downloads the libraries and the Poppler PDF tools;
   `setup_windows.bat lite` skips the local model libraries). It ends with "CiteFilter is ready".
3. Double-click `CiteFilter.bat`.

### macOS / Linux

Needs Python 3.10+ and Poppler (`brew install poppler` or `apt install poppler-utils`).

```bash
git clone https://github.com/harshit2000-10/CiteFilter.git
cd CiteFilter
pip install -r requirements.txt
python3 citefilter_ui.py
```

## How to use it

### 1. Get your two inputs ready

- **Your draft**: a Word file (`.docx`). `.md`, `.tex` and `.txt` also work. Give the sections real headings
  (Heading 1/2 in Word); suggestions are made per section. If the draft has a reference list, CiteFilter
  uses it to tell which papers you already cite.
- **Your Zotero library**: either
  - leave Zotero 7 running and use **From Zotero…** (turn it on once: Zotero > Settings > Advanced >
    tick *Allow other applications on this computer to communicate with Zotero*), or
  - export a CSV: in Zotero select the papers (or a collection), right-click > *Export…* > format **CSV**.
    Keep the exported file where it is; PDFs are found through its *File Attachments* column.

Papers with a PDF attached are judged on abstract and introduction, and can give figures and emails.
Papers without one are judged on title and abstract only.

### 2. Run it

1. Press **Browse…** next to the draft and pick your file.
2. Load the library: press **From Zotero…** and choose the whole library or one collection, or **Browse…** to a CSV.
3. Set **Figures suggested per section** (default 3).
4. Optional: tick **Match papers by meaning too** to add the local SPECTER2 model. The first use downloads
   about 0.9 GB, later runs reuse it. Slower, usually better at synonyms. Not available in the lite edition.
5. Press **Run**. The progress box shows what it is doing; a few minutes for a library of a few hundred papers.
6. Press **Open report** (the web page) or **Open table** (the same data as a spreadsheet).

### 3. Read the report

For each section of your draft, the report lists:

- **Suggested papers**, best first, each with a match %, a short reason and a tag:

  | Tag | Meaning |
  |---|---|
  | strong match | 60% or more |
  | possible match | 40% to 60% |
  | weak match | below 40% |
  | check | below 40% but the paper has no abstract, so check it by hand |

  With word matching, 100% is the best paper in your library for that section, so the % is relative.
  It is similarity, not a probability that the paper is relevant.
- **Cited / not cited yet**: whether your draft already cites the paper. A strong match that is not cited
  yet is worth a look.
- **Suggested figures**: cropped from the PDF with the caption, the paper's citation, the corresponding
  author, the email address found and the licence if OpenAlex knows it, and a draft permission email.
  Click a figure to open its PDF at that page.

After the sections, every paper is listed again under strong, possible and weak match.

`papers.csv` has one row per paper: rank, match, match %, best section, cited in draft, title, year, DOI,
corresponding author, email and how it was found, licence.

### 4. Ask for permission

The draft emails contain placeholders: `[YOUR NAME]`, `[YOUR AFFILIATION]`, `[ARTICLE TITLE]`,
`[TARGET JOURNAL]`, `[YOUR EMAIL]`. Fill them in and send the email yourself; CiteFilter sends nothing.
Check the address and the licence first. For most journal papers the **publisher**, not the author, grants
reuse permission, and email addresses are best guesses.

### Where files go

| What | Where |
|---|---|
| Report for a CSV you browsed to | a `…_report` folder next to that CSV |
| Library loaded with **From Zotero…** and its report | `Documents\CiteFilter` (Windows), `~/CiteFilter` (macOS) |
| Saved AI settings | `%APPDATA%\CiteFilter\llm.env` (Windows), `~/Library/Application Support/CiteFilter/llm.env` (macOS) |

## Optional AI mode

Works with the **Settings…** button under *AI assist*. Enter any OpenAI-style endpoint, a model name and a key
(leave the key empty for a local Ollama), and tick *Save* to keep them. AI then rates papers more carefully,
picks figures and writes a personalised email for each author. Without it, everything above still works.
Setting names are in [llm.env.example](llm.env.example). Never share your `llm.env`: it holds your key.

## Command line

```bash
python3 zotero_filter.py draft.docx library.csv
python3 zotero_filter.py draft.docx zotero              # a running Zotero 7, whole library
python3 zotero_filter.py draft.docx zotero:"My review"  # one Zotero collection
python3 zotero_filter.py draft.docx library.csv --figs 5 --semantic
python3 zotero_filter.py                                # built-in self-check
```

AI options: `--llm-url`, `--llm-model`, `--llm-key`, `--llm-file`.
For the local model also run `pip install torch adapters`.

## Troubleshooting

| Problem | What to do |
|---|---|
| "Could not reach Zotero" | Open Zotero 7 and tick *Allow other applications on this computer to communicate with Zotero* |
| "Poppler not found" (source install) | Windows: run `setup_windows.bat` again. macOS/Linux: install Poppler (see above) |
| No figures or emails for a paper | It has no PDF attached in Zotero, or the PDF has no text layer (scans) |
| Everything lands in one section | The draft has no real headings; use Heading 1/2 styles in Word |
| `.doc` file rejected | Save it as `.docx` first |
| Setup stops on a download | Check the internet connection and run `setup_windows.bat` again |

## What leaves your computer

| When | What is sent | Where |
|---|---|---|
| Always | DOIs of the suggested papers | OpenAlex |
| Local model, first use only | A model download request | Hugging Face |
| AI mode, only if you set an endpoint | Excerpts of your draft, abstracts, starts of introductions, figure captions | The endpoint you chose |

Without AI mode, your draft text never leaves your computer.

## Status

Early and lightly tested. A high match % is not proof of relevance and a low one is not proof of irrelevance.

- Developed on a Mac (Apple Silicon) with a small test library; 84 automated checks pass there.
- The Windows build is produced and self-tested on a clean Windows machine by GitHub Actions (see the Actions tab).
- The Zotero connection and AI mode have only been tested against stand-in servers, not yet against a real Zotero or a real model.

## Build the installer yourself

On Windows, after `setup_windows.bat` worked and `CiteFilter.bat` opens:

1. Install [Inno Setup](https://jrsoftware.org/isdl.php) (free).
2. Double-click `build_windows.bat` (`build_windows.bat lite` for the edition without the local model).

You get `dist\CiteFilter\CiteFilter.exe` (runs without installing) and `dist\CiteFilter-Setup.exe`.
Or let GitHub do it: Actions > *Windows build* > Run workflow; pushing a `v*` tag also attaches
the installers to a release.

## Built with

Python, scikit-learn, python-docx, Tkinter, [Poppler](https://poppler.freedesktop.org/) (run as a separate
program), [OpenAlex](https://openalex.org/), and optionally [SPECTER2](https://huggingface.co/allenai/specter2)
through `transformers` and `adapters`.

## Licence

MIT, see [LICENSE](LICENSE). Software CiteFilter relies on keeps its own licence; see
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Poppler in particular is GPL and is run as a separate program.
