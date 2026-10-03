#!/usr/bin/env python3
"""Desktop patcher GUI for the Disney-Pixar Cars Wii Trilogy.

Supports drag-and-drop or file browsing for WBFS / ISO disc images or main.dol files.
Provides options for Classic Controller, GameCube Controller, Pitstop Skip, and FOV fixes.
"""
import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import disc
import features
import patcher
from dol import Dol
from regions import ALL_REGIONS, GAMES, game_for_region


class CarsPatcherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cars Trilogy Wii Patcher")
        self.geometry("640x660")
        self.minsize(580, 600)

        # State
        self.file_path = None
        self.is_disc = False
        self.region_id = None
        self.feature_vars = {}

        self._build_ui()

    def _build_ui(self):
        # 1. Header / Logo Banner
        banner_frame = tk.Frame(self, bg="#111", height=100)
        banner_frame.pack(fill=tk.X)

        logo_path = os.path.join(HERE, '..', 'assets', 'logo.png')
        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                logo_lbl = tk.Label(banner_frame, image=self.logo_img, bg="#111")
                logo_lbl.pack(side=tk.LEFT, padx=15, pady=10)
            except Exception:
                pass

        header_text_frame = tk.Frame(banner_frame, bg="#111")
        header_text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=15)

        title_lbl = tk.Label(header_text_frame, text="Cars Trilogy Wii Patcher",
                             font=("Helvetica", 18, "bold"), fg="#FFF", bg="#111")
        title_lbl.pack(anchor=tk.W)
        sub_lbl = tk.Label(header_text_frame,
                           text="Classic Controller & GameCube Controller Suite (Cars 1, 2, 3)",
                           font=("Helvetica", 11), fg="#BBB", bg="#111")
        sub_lbl.pack(anchor=tk.W)

        # 2. File Selection Frame
        file_frame = tk.LabelFrame(self, text=" Target Disc Image or main.dol ", font=("Helvetica", 11, "bold"), padx=12, pady=10)
        file_frame.pack(fill=tk.X, padx=15, pady=10)

        self.path_entry = tk.Entry(file_frame, font=("Helvetica", 11))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        browse_btn = tk.Button(file_frame, text="Browse...", command=self._browse_file, font=("Helvetica", 10, "bold"))
        browse_btn.pack(side=tk.RIGHT)

        # Info label
        self.info_lbl = tk.Label(file_frame, text="Please select a Cars WBFS, ISO, or main.dol file.",
                                 font=("Helvetica", 10, "italic"), fg="#555")
        self.info_lbl.pack(fill=tk.X, anchor=tk.W, pady=(8, 0))

        # 3. Patch Options Frame
        self.opt_frame = tk.LabelFrame(self, text=" Patch Options ", font=("Helvetica", 11, "bold"), padx=12, pady=10)
        self.opt_frame.pack(fill=tk.X, padx=15, pady=5)

        for fkey in features.FEATURES:
            var = tk.BooleanVar(value=True)
            self.feature_vars[fkey] = var
            cb = tk.Checkbutton(self.opt_frame, text=features.TITLES[fkey], variable=var,
                                font=("Helvetica", 11), anchor=tk.W)
            cb.pack(fill=tk.X, anchor=tk.W, pady=2)
            desc_lbl = tk.Label(self.opt_frame, text=f"    {features.DESCRIPTIONS[fkey]}",
                                font=("Helvetica", 9), fg="#666", anchor=tk.W)
            desc_lbl.pack(fill=tk.X, anchor=tk.W, pady=(0, 4))

        # 4. Action Button
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=15, pady=10)

        self.patch_btn = tk.Button(btn_frame, text="Apply Patches", command=self._start_patching,
                                   bg="#007ACC", fg="#FFF", font=("Helvetica", 13, "bold"),
                                   state=tk.DISABLED, pady=6)
        self.patch_btn.pack(fill=tk.X)

        # 5. Log Console
        log_frame = tk.LabelFrame(self, text=" Output Log ", font=("Helvetica", 10, "bold"), padx=8, pady=6)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 10), height=8, bg="#F9F9F9")
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

    def log(self, text):
        self.log_text.insert(tk.END, text + "\n")
        self.log_text.see(tk.END)

    def _browse_file(self):
        f = filedialog.askopenfilename(
            title="Select Cars Disc Image or main.dol",
            filetypes=[
                ("All Supported Files", "*.wbfs;*.iso;*.dol"),
                ("Wii Disc Images", "*.wbfs;*.iso"),
                ("Executable DOL", "*.dol"),
                ("All Files", "*.*")
            ]
        )
        if f:
            self._load_file(f)

    def _load_file(self, path):
        self.file_path = path
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

        ext = os.path.splitext(path)[1].lower()
        if ext in ('.wbfs', '.iso'):
            self.is_disc = True
            # Read disc id using wit
            wit_bin = disc.find_wit()
            if not wit_bin:
                self.log("Note: wit is required to extract and rebuild disc images.")
            self.info_lbl.config(text=f"Selected Disc: {os.path.basename(path)}", fg="#006600")
            self.patch_btn.config(state=tk.NORMAL)
        elif ext == '.dol':
            self.is_disc = False
            try:
                d = Dol(path)
                reg = patcher.detect_region(d)
                if reg:
                    self.region_id = reg
                    meta = ALL_REGIONS[reg]
                    self.info_lbl.config(text=f"Detected DOL: {reg} - {meta['label']}", fg="#006600")
                    self.patch_btn.config(state=tk.NORMAL)
                else:
                    self.info_lbl.config(text="Could not identify Cars region from this main.dol.", fg="#990000")
                    self.patch_btn.config(state=tk.DISABLED)
            except Exception as e:
                self.info_lbl.config(text=f"Error reading DOL: {e}", fg="#990000")
                self.patch_btn.config(state=tk.DISABLED)

    def _start_patching(self):
        if not self.file_path:
            return

        selected = [k for k, v in self.feature_vars.items() if v.get()]
        if not selected:
            messagebox.showwarning("No Patches Selected", "Please tick at least one patch option.")
            return

        self.patch_btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.log("Starting patch process...")

        def worker():
            try:
                if self.is_disc:
                    disc.run_patch(self.file_path, self.log, self._patch_finished, which=selected)
                else:
                    d = Dol(self.file_path)
                    applied = patcher.patch(d, self.region_id, selected)
                    out_path = self.file_path.replace('.dol', '_patched.dol')
                    d.save(out_path)
                    self.log(f"Successfully applied: {', '.join(applied)}")
                    self.log(f"Saved patched DOL to: {out_path}")
                    self._patch_finished(True, out_path)
            except Exception as e:
                self.log(f"ERROR: {e}")
                self._patch_finished(False, str(e))

        t = threading.Thread(target=worker, daemon=True)
        t.start()

    def _patch_finished(self, success, result):
        def cb():
            self.patch_btn.config(state=tk.NORMAL)
            if success:
                messagebox.showinfo("Success", f"Patching completed successfully!\n\nTarget: {result}")
            else:
                messagebox.showerror("Patching Failed", f"An error occurred during patching:\n\n{result}")
        self.after(0, cb)


if __name__ == '__main__':
    app = CarsPatcherApp()
    app.mainloop()
