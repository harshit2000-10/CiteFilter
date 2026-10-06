#!/usr/bin/env python3
"""CiteFilter desktop window: pick a draft and a Zotero CSV, run, open the report.

Start:  Windows: double-click CiteFilter.bat (after setup_windows.bat) or the installed CiteFilter
        any system: python3 citefilter_ui.py
All the work is done by zotero_filter.py; this file is only the window.
"""
import contextlib
import importlib
import io
import multiprocessing
import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, font as tkfont, ttk

import zotero_filter as core

HERE = Path(__file__).parent
LLM_FILE = core.config_dir() / "llm.env"
MAC = sys.platform == "darwin"
FONT_SCALE = 1.0 if MAC else 0.75  # Tk points are 1/72 inch: a 13 pt font is 13 px on a Mac but 17 px on Windows
MONO, HAND = ("Menlo", "pointinghand") if MAC else ("Consolas", "hand2")
DRAFT_TYPES = [("Review draft", "*.docx *.md *.tex *.txt"), ("All files", "*")]
CSV_TYPES = [("Zotero CSV export", "*.csv"), ("All files", "*")]

# Palette (matches the logo)
NAVY, TEAL, TEAL_DARK, AMBER = "#17324D", "#1A9E8F", "#157F73", "#F5A623"
BG, CARD, BORDER, FIELD = "#F1F4F8", "#FFFFFF", "#DCE3EC", "#F8FAFC"
TEXT, MUTED, FAINT = "#0F172A", "#64748B", "#A3AEBD"


def rounded(x1, y1, x2, y2, r):
    """Points for a smooth canvas polygon that draws a rounded rectangle."""
    return [x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y1 + r,
            x2, y2 - r, x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2, x1 + r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1]


class RoundButton(tk.Canvas):
    """Rounded button drawn on a canvas (ttk has no rounded buttons)."""

    def __init__(self, parent, text, command, font, primary=False, height=36):
        width = font.measure(text) + (44 if primary else 32)
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0)
        self.command, self.primary, self.enabled, self.hover = command, primary, True, False
        self.shape = self.create_polygon(rounded(1, 1, width - 1, height - 1, 9), smooth=True)
        self.label = self.create_text(width / 2, height / 2, text=text, font=font)
        self.bind("<Button-1>", lambda _: self.invoke())
        self.bind("<Enter>", lambda _: self.paint(hover=True))
        self.bind("<Leave>", lambda _: self.paint(hover=False))
        self.paint()

    def paint(self, hover=None):
        self.hover = self.hover if hover is None else hover
        lit = self.hover and self.enabled
        if self.primary:
            fill = (TEAL_DARK if lit else TEAL) if self.enabled else "#A9D9D3"
            outline, ink = fill, "#FFFFFF"
        else:
            fill, outline = ("#EEF2F7" if lit else CARD), BORDER
            ink = TEXT if self.enabled else FAINT
        self.itemconfigure(self.shape, fill=fill, outline=outline)
        self.itemconfigure(self.label, fill=ink)
        self.configure(cursor=HAND if self.enabled else "arrow")

    def set_enabled(self, enabled):
        self.enabled = enabled
        self.paint()

    def invoke(self):
        if self.enabled:
            self.command()


class QueueWriter:
    """Stands in for stdout in the worker thread; the window drains the queue."""

    def __init__(self, events):
        self.events = events

    def write(self, text):
        self.events.put(("log", text))

    def flush(self):
        pass


class App:
    def __init__(self, root):
        self.root, self.events, self.report_dir = root, queue.Queue(), None
        root.title("CiteFilter")
        root.configure(bg=BG)
        with contextlib.suppress(tk.TclError):  # keep the title bar light to match; older Tk lacks this
            root.tk.call("tk::unsupported::MacWindowStyle", "appearance", root, "aqua")
        family = tkfont.nametofont("TkDefaultFont").actual("family")
        font = lambda size, weight="normal": tkfont.Font(family=family, size=max(8, round(size * FONT_SCALE)), weight=weight)
        self.f_body, self.f_small, self.f_bold = font(13), font(11), font(13, "bold")
        self.f_title, self.f_brand, self.f_brand_light = font(15, "bold"), font(26, "bold"), font(26)
        self.style()

        self.images = [tk.PhotoImage(file=str(HERE / "logo" / name))
                       for name in ("citefilter_icon.png", "citefilter_icon_44.png")]
        root.iconphoto(True, self.images[0])

        header = tk.Frame(root, bg=NAVY)
        header.pack(fill="x")
        tk.Label(header, image=self.images[1], bg=NAVY).pack(side="left", padx=(24, 12), pady=14)
        cite_width = self.f_brand.measure("Cite")  # one canvas so the two halves of the name touch
        brand = tk.Canvas(header, bg=NAVY, highlightthickness=0, height=44,
                          width=cite_width + self.f_brand_light.measure("Filter") + 4)
        brand.create_text(0, 22, anchor="w", text="Cite", font=self.f_brand, fill="#FFFFFF")
        brand.create_text(cite_width + 1, 22, anchor="w", text="Filter", font=self.f_brand_light, fill="#4FD1C1")
        brand.pack(side="left")
        tk.Label(header, text="Papers and figures for your article, suggested", font=self.f_small,
                 bg=NAVY, fg="#9FB3C8").pack(side="right", padx=24)

        body = tk.Frame(root, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(18, 20))

        saved = core.read_env_file(LLM_FILE) if LLM_FILE.is_file() else {}
        setting = lambda name: saved.get(name) or os.environ.get(name, "")
        self.draft, self.library = tk.StringVar(), tk.StringVar()
        self.figs, self.semantic = tk.IntVar(value=3), tk.BooleanVar(value=False)
        self.url, self.model = tk.StringVar(value=setting("LLM_BASE_URL")), tk.StringVar(value=setting("LLM_MODEL"))
        self.key, self.save = tk.StringVar(value=setting("LLM_API_KEY")), tk.BooleanVar(value=False)

        files = self.card(body, "Your files")
        files.columnconfigure(0, weight=1)
        self.field(files, 0, "Your draft, research or review article  (.docx, .md, .tex, .txt)", self.draft, span=2, browse=DRAFT_TYPES)
        self.field(files, 2, "Zotero library  (load it from Zotero, or browse to a CSV export)", self.library,
                   browse=CSV_TYPES)
        RoundButton(files, "From Zotero…", self.pick_zotero, self.f_body).grid(row=3, column=1, padx=(10, 0))
        row = tk.Frame(files, bg=CARD)
        row.grid(row=4, column=0, columnspan=3, sticky="w", pady=(12, 0))
        tk.Label(row, text="Figures suggested per section", font=self.f_body, bg=CARD, fg=TEXT).pack(side="left")
        ttk.Spinbox(row, from_=1, to=10, width=4, textvariable=self.figs, font=self.f_body).pack(side="left", padx=10)

        ttk.Checkbutton(files, text="Match papers by meaning too  (SPECTER2 local model: runs on this computer, nothing is sent out)",
                        variable=self.semantic).grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))

        ai = self.card(body, "AI assist", "Optional")
        RoundButton(ai.head, "Settings…", self.ai_settings, self.f_small, height=28).pack(side="right")
        self.ai_status = tk.Label(ai, font=self.f_small, bg=CARD, fg=MUTED, anchor="w")
        self.ai_status.pack(fill="x")
        for var in (self.url, self.model):
            var.trace_add("write", lambda *_: self.show_ai_status())
        self.show_ai_status()

        actions = tk.Frame(body, bg=BG)
        actions.pack(fill="x", pady=(2, 14))
        self.run_button = RoundButton(actions, "Run", self.run, self.f_bold, primary=True)
        self.run_button.pack(side="left")
        self.report_button = RoundButton(actions, "Open report", lambda: self.open(self.report_dir / "report.html"), self.f_body)
        self.report_button.pack(side="left", padx=10)
        self.table_button = RoundButton(actions, "Open table", lambda: self.open(self.report_dir / "papers.csv"), self.f_body)
        self.table_button.pack(side="left")
        self.report_button.set_enabled(False)
        self.table_button.set_enabled(False)
        self.status = tk.Label(actions, text="Ready", font=self.f_body, bg=BG, fg=MUTED)
        self.status.pack(side="right")
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=120)

        progress = self.card(body, "Progress", expand=True)
        self.log = tk.Text(progress, height=7, wrap="word", state="disabled", relief="flat", bd=0,
                           bg=FIELD, fg=TEXT, font=(MONO, max(8, round(11 * FONT_SCALE))), padx=12, pady=10,
                           highlightthickness=1, highlightbackground=BORDER, highlightcolor=BORDER)
        self.log.pack(fill="both", expand=True)
        self.say("Pick your draft and your Zotero library, then press Run.\n")

        self.fit(place=True)
        root.after(100, self.poll)

    def fit(self, place=False):
        """Size the window to its content, never taller than the screen."""
        self.root.update_idletasks()
        screen_w, screen_h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        width = 780 if place else self.root.winfo_width()
        height = min(self.root.winfo_reqheight(), screen_h - 110)
        self.root.minsize(700, min(height, 520))
        x = (screen_w - width) // 2 if place else self.root.winfo_x()
        y = (screen_h - height) // 3 if place else self.root.winfo_y()
        y = max(30, min(y, screen_h - height - 80))  # growing must not push the bottom off the screen
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def show_ai_status(self):
        url, model = self.url.get().strip(), self.model.get().strip()
        self.ai_status.configure(
            text=f"On: model {model} at {url}" if url and model else
            "Not complete: AI needs both an endpoint URL and a model name" if url or model else
            "Off. Papers are rated by word matching, plus the local model if ticked above.",
            fg=TEAL_DARK if url and model else MUTED)

    def ai_settings(self):
        """The AI fields live in their own small window so the main one fits small screens."""
        top = tk.Toplevel(self.root, bg=CARD, padx=20, pady=16)
        top.title("AI settings")
        top.transient(self.root)
        top.update_idletasks()
        with contextlib.suppress(tk.TclError):
            top.tk.call("tk::unsupported::MacWindowStyle", "appearance", top, "aqua")
        top.geometry(f"+{self.root.winfo_rootx() + 90}+{self.root.winfo_rooty() + 110}")
        top.columnconfigure(0, weight=1, uniform="ai")
        top.columnconfigure(1, weight=1, uniform="ai")
        tk.Label(top, text="Any OpenAI-style endpoint. Leave everything empty to run without AI.",
                 font=self.f_body, bg=CARD, fg=TEXT).grid(row=0, column=0, columnspan=2, sticky="w")
        self.field(top, 1, "Endpoint URL, for example http://localhost:11434/v1", self.url, span=2)
        self.field(top, 3, "Model name", self.model, column=0, pad=(0, 8))
        self.field(top, 3, "API key (not needed for a local model)", self.key, column=1, pad=(8, 0), show="•")
        ttk.Checkbutton(top, text="Save these for next time (the key is stored as plain text on this computer)",
                        variable=self.save).grid(row=5, column=0, columnspan=2, sticky="w", pady=(14, 0))
        tk.Label(top, text="With AI on, excerpts of your draft, the abstracts and the captions are sent to this endpoint.",
                 font=self.f_small, bg=CARD, fg=MUTED, wraplength=560, justify="left").grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(6, 12))
        RoundButton(top, "Done", top.destroy, self.f_bold, primary=True).grid(row=7, column=1, sticky="e")
        top.grab_set()
        return top

    def style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")  # the native macOS theme ignores colours
        for name in ("TEntry", "TSpinbox"):
            style.configure(name, fieldbackground=FIELD, foreground=TEXT, insertcolor=TEXT, padding=8,
                            bordercolor=BORDER, lightcolor=FIELD, darkcolor=FIELD, relief="flat",
                            selectbackground="#BFE8E2", selectforeground=TEXT, arrowcolor=MUTED, background=CARD)
            style.map(name, bordercolor=[("focus", TEAL)], lightcolor=[("focus", FIELD)], darkcolor=[("focus", FIELD)])
        style.configure("TCheckbutton", background=CARD, foreground=TEXT, font=self.f_body, focuscolor=CARD,
                        indicatorbackground=FIELD, indicatorforeground="#FFFFFF", bordercolor=BORDER,
                        upperbordercolor=BORDER, lowerbordercolor=BORDER)
        style.map("TCheckbutton", background=[("active", CARD)],
                  indicatorbackground=[("selected", TEAL), ("active", "#EEF2F7")])
        style.configure("Horizontal.TProgressbar", troughcolor=BORDER, background=TEAL, bordercolor=BG,
                        lightcolor=TEAL, darkcolor=TEAL, thickness=6)

    def card(self, parent, title, note="", expand=False):
        """A white panel with a heading; returns the frame to put content in."""
        outer = tk.Frame(parent, bg=CARD, highlightbackground=BORDER, highlightcolor=BORDER, highlightthickness=1)
        outer.pack(fill="both" if expand else "x", expand=expand, pady=(0, 14))
        head = tk.Frame(outer, bg=CARD)
        head.pack(fill="x", padx=18, pady=(14, 10))
        tk.Label(head, text=title, font=self.f_title, bg=CARD, fg=TEXT).pack(side="left")
        tk.Label(head, text=note, font=self.f_small, bg=CARD, fg=MUTED).pack(side="left", padx=10, pady=(3, 0))
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="both", expand=expand, padx=18, pady=(0, 16))
        inner.head = head  # lets a caller put its own control in the heading row
        return inner

    def field(self, parent, row, label, var, column=0, span=1, pad=(0, 0), show="", browse=None):
        """Small label above a text box, with an optional Browse button beside it."""
        tk.Label(parent, text=label, font=self.f_small, bg=CARD, fg=MUTED).grid(
            row=row, column=column, columnspan=span, sticky="w", padx=pad, pady=(8, 3))
        ttk.Entry(parent, textvariable=var, show=show, font=self.f_body, width=30).grid(
            row=row + 1, column=column, columnspan=span, sticky="ew", padx=pad)
        if browse:  # always in the third column, so a row may put one more button in the second
            RoundButton(parent, "Browse…", lambda: var.set(filedialog.askopenfilename(filetypes=browse) or var.get()),
                        self.f_body).grid(row=row + 1, column=2, padx=(10, 0))

    def pick_zotero(self):
        """Ask a running Zotero for its collections, then load the chosen one."""
        try:
            choices = [(None, "Whole library")] + core.zotero_collections()
        except core.ZoteroError as err:
            return self.say(f"\n{err}\n")
        top = tk.Toplevel(self.root, bg=CARD, padx=18, pady=16)
        top.title("Load from Zotero")
        top.transient(self.root)
        top.update_idletasks()  # the window must exist before its title bar style can be set
        with contextlib.suppress(tk.TclError):  # light title bar, like the main window
            top.tk.call("tk::unsupported::MacWindowStyle", "appearance", top, "aqua")
        top.geometry(f"+{self.root.winfo_rootx() + 150}+{self.root.winfo_rooty() + 120}")
        tk.Label(top, text="Which papers should CiteFilter read?", font=self.f_title, bg=CARD, fg=TEXT).pack(anchor="w")
        box = tk.Listbox(top, font=self.f_body, height=min(len(choices), 12), width=44, activestyle="none",
                         bg=FIELD, fg=TEXT, selectbackground="#BFE8E2", selectforeground=TEXT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=TEAL, exportselection=False)
        box.insert("end", *(name for _, name in choices))
        box.selection_set(0)
        box.pack(fill="both", expand=True, pady=12)

        def load(_=None):
            key, name = choices[(box.curselection() or (0,))[0]]
            top.destroy()
            self.load_zotero(key, name)

        box.bind("<Double-Button-1>", load)
        RoundButton(top, "Load", load, self.f_bold, primary=True).pack(anchor="e")
        top.grab_set()
        return top, box, load  # handed back so a test can drive the dialog

    def load_zotero(self, key, name):
        try:
            path, count, with_pdf = core.zotero_export(key, name)
        except core.ZoteroError as err:
            return self.say(f"\n{err}\n")
        self.library.set(str(path))
        self.say(f"\nLoaded {count} papers from Zotero ({name}); {with_pdf} have a PDF on this computer.\n"
                 f"Saved as {path}\n")

    def say(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.configure(state="disabled")

    def busy(self, running, status, colour=MUTED):
        self.run_button.set_enabled(not running)
        self.status.configure(text=status, fg=colour)
        if running:
            self.progress.pack(side="right", padx=12)
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.pack_forget()

    @staticmethod
    def open(path):
        """Open a file with whatever the system uses for it (browser for the report, spreadsheet for the table)."""
        if sys.platform == "win32":
            os.startfile(str(path))
        else:
            subprocess.run(["open" if MAC else "xdg-open", str(path)], check=False)

    def run(self):
        draft, library = self.draft.get().strip(), self.library.get().strip()
        url, model, key = self.url.get().strip().rstrip("/"), self.model.get().strip(), self.key.get().strip()
        for label, path in (("Draft", draft), ("Zotero library", library)):
            if not Path(path).is_file():
                return self.say(f"\n{label}: file not found. Use Browse to pick it.\n")
        try:
            figs = max(1, int(self.figs.get()))
        except (tk.TclError, ValueError):
            return self.say("\nFigures per section must be a number.\n")
        if bool(url) != bool(model):
            return self.say("\nAI needs both the endpoint URL and the model name. Fill both, or clear both.\n")
        if self.save.get():
            LLM_FILE.parent.mkdir(parents=True, exist_ok=True)
            LLM_FILE.write_text(f"LLM_BASE_URL={url}\nLLM_MODEL={model}\nLLM_API_KEY={key}\n", encoding="utf-8")
            LLM_FILE.chmod(0o600)  # owner-only; has no effect on Windows
        config = (url, model, key) if url else None

        self.report_button.set_enabled(False)
        self.table_button.set_enabled(False)
        self.busy(True, "Running…")
        self.say(f"\nRunning: word matching{' + local model' if self.semantic.get() else ''}"
                 f"{' + AI' if config else ''}...\n")
        threading.Thread(target=self.work, args=(draft, library, figs, config, self.semantic.get()),
                         daemon=True).start()

    def work(self, draft, library, figs, config, semantic):
        """Runs in a background thread: never touches widgets, only the queue."""
        try:
            with contextlib.redirect_stdout(QueueWriter(self.events)):
                out = core.main(draft, library, figs, config, semantic)
            self.events.put(("done", out))
        except (Exception, SystemExit) as err:  # show any failure in the window, keep it open
            self.events.put(("error", f"{type(err).__name__}: {err}"))

    def poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "log":
                    self.say(value)
                elif kind == "done":
                    self.report_dir = Path(value)
                    self.busy(False, "Done", TEAL_DARK)
                    self.report_button.set_enabled(True)
                    self.table_button.set_enabled(True)
                    self.say("Done. Opening the report.\n")
                    self.open(self.report_dir / "report.html")
                else:
                    self.busy(False, "Could not finish", "#B42318")
                    self.say(f"\nCould not finish: {value}\n")
        except queue.Empty:
            pass
        self.root.after(100, self.poll)


def selftest(report):
    """Check a packaged app without opening a window: write what works to a file, exit 0 or 1."""
    lines, ok = [], True
    try:
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            core.demo()
        lines += [printed.getvalue().strip(), f"version {core.VERSION}", f"pdftotext: {core.tool('pdftotext')}"]
        ok = bool(core.tool("pdftotext") and core.tool("pdftoppm"))
    except Exception as err:
        lines, ok = lines + [f"FAILED: {type(err).__name__}: {err}"], False
    for name in ("torch", "transformers", "adapters"):  # only in the full edition
        try:
            lines.append(f"{name} {importlib.import_module(name).__version__}")
        except Exception as err:
            lines.append(f"{name}: not available ({type(err).__name__})")
    Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.exit(0 if ok else 1)


def main():
    multiprocessing.freeze_support()  # a packaged Windows app would otherwise keep relaunching itself
    for stream in ("stdout", "stderr"):  # a windowed app has no console, but libraries still write to these
        if getattr(sys, stream) is None:
            setattr(sys, stream, open(os.devnull, "w"))
    if "--selftest" in sys.argv:
        selftest((sys.argv[sys.argv.index("--selftest") + 1:] or ["selftest.txt"])[0])
    if sys.platform == "win32":
        import ctypes

        with contextlib.suppress(Exception):
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # sharp text on high-resolution screens
        with contextlib.suppress(Exception):
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CiteFilter")  # own taskbar icon
    window = tk.Tk()
    App(window)
    window.mainloop()


if __name__ == "__main__":
    main()
