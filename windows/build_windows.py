"""Package CiteFilter for Windows: dist\\CiteFilter\\CiteFilter.exe, then CiteFilter-Setup.exe.

Run it through build_windows.bat, after setup_windows.bat has finished and CiteFilter.bat works.

    build_windows.bat          full edition (local model libraries inside; large)
    build_windows.bat lite     without PyTorch, transformers and adapters

The installer step needs Inno Setup (free): https://jrsoftware.org/isdl.php
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
MODEL_PACKAGES = ("torch", "transformers", "adapters", "tokenizers")
# transformers checks the installed version of these at start-up, so their metadata must be packed too
METADATA = ("torch", "transformers", "adapters", "tokenizers", "huggingface-hub", "safetensors", "regex",
            "requests", "packaging", "filelock", "numpy", "tqdm", "pyyaml")


def pyinstaller_args(lite):
    data = lambda source, target: ["--add-data", f"{ROOT / source}{os.pathsep}{target}"]
    args = ["--noconfirm", "--clean", "--windowed", "--name", "CiteFilter",
            "--icon", str(ROOT / "logo" / "citefilter.ico"),
            *data("logo", "logo"), *data("poppler", "poppler"), *data("llm.env.example", "."),
            "--collect-data", "docx"]
    if lite:
        for package in MODEL_PACKAGES:
            args += ["--exclude-module", package]
    else:
        for package in ("transformers", "adapters", "tokenizers"):
            args += ["--collect-all", package]
        for package in METADATA:
            args += ["--copy-metadata", package]
    return [*args, str(ROOT / "citefilter_ui.py")]


def find_inno_setup():
    candidates = [shutil.which("iscc")] + [
        str(Path(os.environ.get(var, "")) / "Inno Setup 6" / "ISCC.exe")
        for var in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA")]
    return next((c for c in candidates if c and Path(c).is_file()), None)


def main(args):
    lite = "lite" in args
    if not PYTHON.is_file():
        raise SystemExit("Run setup_windows.bat first.")
    if not (ROOT / "poppler").is_dir():
        raise SystemExit("The poppler folder is missing. Run setup_windows.bat first.")
    print(f"[1/3] PyInstaller ({'lite' if lite else 'full'} edition; the full one takes several minutes)", flush=True)
    subprocess.run([str(PYTHON), "-m", "pip", "install", "--disable-pip-version-check", "pyinstaller"], check=True)
    subprocess.run([str(PYTHON), "-m", "PyInstaller", *pyinstaller_args(lite)], cwd=ROOT, check=True)
    app = ROOT / "dist" / "CiteFilter" / "CiteFilter.exe"
    print(f"\n[2/3] built {app}\n      Start it once and do a test run before going on.", flush=True)

    inno = find_inno_setup()
    if not inno:
        print("\n[3/3] Inno Setup not found, so no installer was made. Install it from\n"
              "      https://jrsoftware.org/isdl.php and run build_windows.bat again.\n"
              "      Until then, the whole dist\\CiteFilter folder can be zipped and copied to another PC.")
        return
    subprocess.run([inno, str(ROOT / "windows" / "installer.iss")], check=True)
    print(f"\n[3/3] installer: {ROOT / 'dist' / 'CiteFilter-Setup.exe'}")


if __name__ == "__main__":
    try:
        main([a.lower() for a in sys.argv[1:]])
    except subprocess.CalledProcessError as err:
        raise SystemExit(f"\nA step failed: {' '.join(map(str, err.cmd))[:300]}\n"
                         "Copy the messages above and send them back.")
