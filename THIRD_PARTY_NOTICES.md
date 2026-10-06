# Third-party software

CiteFilter's own code is under the MIT licence (see `LICENSE`). It uses the software below, each
under its own licence. The source repository contains none of it; the Windows installer does.
Licence names are given for orientation; the full text is with each project.

## Shipped as a separate program

**Poppler** (`pdftotext`, `pdftoppm`), GNU General Public License, version 2 or later.
CiteFilter starts these programs and reads their output; it is not linked with them.
Source code: <https://poppler.freedesktop.org/>.
The Windows binaries in the installer are the unmodified build published at
<https://github.com/oschwartz10612/poppler-windows/releases>, where the matching sources and
build scripts are available.

## Python and libraries inside the Windows app

| Software | Licence |
|---|---|
| Python, Tcl/Tk | PSF licence, Tcl/Tk licence (BSD-style) |
| scikit-learn, NumPy, SciPy, joblib, threadpoolctl | BSD 3-clause |
| python-docx | MIT |
| lxml | BSD 3-clause |
| PyTorch (full edition) | BSD 3-clause |
| transformers, adapters, tokenizers, safetensors, huggingface_hub (full edition) | Apache 2.0 |

## Downloaded when used, not included

**SPECTER2** model files from the Allen Institute for AI (<https://huggingface.co/allenai/specter2>), Apache 2.0.

## Services

**OpenAlex** (<https://openalex.org/>) for corresponding authors and licences; its data is CC0.
