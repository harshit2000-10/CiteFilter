"""Set CiteFilter up on Windows: a private Python environment, the libraries, Poppler, then a self-check.

Run it through setup_windows.bat (double-click). Running it again is safe: finished steps are skipped.

    setup_windows.bat          everything, including the local model libraries (about 1.5 GB)
    setup_windows.bat lite     without the local model (about 350 MB)
"""
import json
import os
import subprocess
import sys
import urllib.request
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VENV = ROOT / ".venv"
POPPLER_RELEASES = "https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest"


def venv_python():
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def step(number, text):
    print(f"\n[{number}/5] {text}", flush=True)


def pip(*args):
    subprocess.run([str(venv_python()), "-m", "pip", "install", "--disable-pip-version-check", *args], check=True)


def install_poppler(dest=ROOT / "poppler", releases=POPPLER_RELEASES, program="pdftotext.exe"):
    """Put the Windows build of Poppler in ./poppler (skipped if already there); return its program folder."""
    found = sorted(dest.rglob(program)) if dest.is_dir() else []
    if found:
        return found[0].parent
    headers = {"User-Agent": "CiteFilter-setup"}
    if os.environ.get("GITHUB_TOKEN") and releases.startswith("https://api.github.com/"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]  # automated builds: avoids GitHub's anonymous limit
    request = urllib.request.Request(releases, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        release = json.load(response)
    asset = next((a for a in release.get("assets", []) if a["name"].lower().endswith(".zip")), None)
    if not asset:
        raise SystemExit("Could not find the Poppler download. Get the latest zip from\n"
                         "https://github.com/oschwartz10612/poppler-windows/releases\n"
                         f"and unzip it into {dest}")
    archive = dest.parent / asset["name"]
    print(f"    downloading {asset['name']} ({asset.get('size', 0) / 1e6:.0f} MB)...", flush=True)
    urllib.request.urlretrieve(asset["browser_download_url"], archive)
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(dest)
    archive.unlink()
    found = sorted(dest.rglob(program))
    if not found:
        raise SystemExit(f"Poppler was unpacked into {dest} but {program} is not in it.")
    return found[0].parent


def main(args):
    lite = "lite" in args
    if sys.version_info < (3, 10):
        raise SystemExit(f"Python 3.10 or newer is needed; this is {sys.version.split()[0]}. "
                         "Install a newer one from https://www.python.org/downloads/windows/")

    step(1, "private Python environment (.venv folder)")
    if venv_python().is_file():
        print("    already there")
    else:
        venv.create(VENV, with_pip=True)

    step(2, "libraries: scikit-learn, python-docx (about 250 MB)")
    pip("-r", str(ROOT / "requirements.txt"))

    step(3, "local model libraries: PyTorch CPU build, adapters (about 1 GB)")
    if lite:
        print("    skipped (lite). The 'Match papers by meaning too' box will fall back to word matching.")
    else:
        pip("torch", "--index-url", "https://download.pytorch.org/whl/cpu")
        pip("adapters")

    step(4, "Poppler PDF tools (about 45 MB download)")
    print(f"    ready in {install_poppler()}")

    step(5, "self-check")
    check = subprocess.run([str(venv_python()), str(ROOT / "zotero_filter.py")], capture_output=True, text=True)
    if "demo ok" in check.stdout:
        print("    passed\n\nCiteFilter is ready. Double-click CiteFilter.bat to start it.")
    else:
        print("    FAILED. Copy everything below and send it back:\n")
        print(check.stdout[-3000:], check.stderr[-3000:], sep="\n")
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main([a.lower() for a in sys.argv[1:]])
    except subprocess.CalledProcessError as err:
        raise SystemExit(f"\nA step failed: {' '.join(map(str, err.cmd))[:300]}\n"
                         "Check the internet connection and run setup_windows.bat again.")
