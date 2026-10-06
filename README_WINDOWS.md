# CiteFilter on Windows

Status: the code was written and tested on a Mac. The Windows scripts in this folder have **not yet
been run on Windows**. Step 2 below is their first real test. If anything fails, copy the text from
the black window and send it back.

Needs: Windows 10 or 11 (64-bit), 8 GB memory (16 GB recommended), 5 GB free disk, internet for setup.

## 1. Get ready (once)

1. Unzip `CiteFilter-for-Windows.zip` somewhere simple, for example `C:\CiteFilter`.
2. Install Python 3.12 or 3.13 from <https://www.python.org/downloads/windows/>.
   In the installer, tick **Add python.exe to PATH**.

## 2. Set up (once, about 10 minutes)

Double-click **`setup_windows.bat`**. It:

| Step | What | Download |
|---|---|---|
| 1 | Makes a private Python environment in the `.venv` folder | none |
| 2 | Installs scikit-learn and python-docx | ~100 MB |
| 3 | Installs PyTorch (CPU build) and adapters for the local model | ~300 MB |
| 4 | Downloads the Poppler PDF tools into the `poppler` folder | ~45 MB |
| 5 | Runs CiteFilter's self-check | none |

It ends with **"CiteFilter is ready"**. Running it again is safe.

To skip the local model (saves about 1 GB), open a Command Prompt in the folder and run
`setup_windows.bat lite`.

## 3. Start

Double-click **`CiteFilter.bat`**.

The first time you tick "Match papers by meaning too", the SPECTER2 model (about 0.9 GB) is
downloaded; later runs use the saved copy.

Files CiteFilter writes:

- Libraries loaded with "From Zotero…" and their reports: `Documents\CiteFilter`
- Reports for a CSV you browsed to: a `…_report` folder next to that CSV
- AI settings, if you tick Save: `%APPDATA%\CiteFilter\llm.env`

## 4. Things to check on the first runs

1. `setup_windows.bat` finishes with "CiteFilter is ready".
2. The window opens, text is sharp, nothing is cut off.
3. Browse to a Word draft and a Zotero CSV export, press Run, the report opens in the browser.
4. Cropped figures show in the report; clicking one opens the PDF at that page.
5. "From Zotero…" with Zotero 7 open (Settings > Advanced > "Allow other applications on this
   computer to communicate with Zotero"). Note the line "Loaded N papers… M have a PDF".
6. Tick "Match papers by meaning too" and run again.
7. Try a draft or library in a folder whose name has spaces or non-English letters.
8. "Open table" opens `papers.csv` with accents shown correctly.

## 5. Make an installer (optional, after step 4 works)

1. Install Inno Setup (free): <https://jrsoftware.org/isdl.php>
2. Double-click **`build_windows.bat`** (`build_windows.bat lite` for the edition without the local model).

Result:

- `dist\CiteFilter\CiteFilter.exe`: the app with Python and all libraries inside. Test it first.
- `dist\CiteFilter-Setup.exe`: the installer to give to other people.

Packing PyTorch into an app is the step most likely to need fixes. If the full build fails or the
built app cannot load the local model, send back the messages; the lite build is the fallback.

People who download an unsigned installer will see a Windows SmartScreen warning ("More info" >
"Run anyway"). Removing it needs a paid code-signing certificate.

## If something goes wrong

| Message | What to do |
|---|---|
| "Python was not found" | Install Python as in step 1, with "Add python.exe to PATH" ticked |
| Setup stops at step 2 or 3 | Check the internet connection, run `setup_windows.bat` again |
| "Poppler not found" in the Progress box | Run `setup_windows.bat` again |
| "Could not reach Zotero" | Open Zotero 7 and tick the setting named in check 5 |
| Window does not open from `CiteFilter.bat` | Open a Command Prompt in the folder and run `.venv\Scripts\python.exe citefilter_ui.py`; send back what it prints |
