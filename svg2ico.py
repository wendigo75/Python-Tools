# ==============================================================================
# SVG to Icons Converter
# Copyright (c) 2026 Wendigo75
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ==============================================================================

import importlib.util
import io
import os
import re
import subprocess
import sys
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, ttk

def ensure_dependencies() -> bool:
    required = {"cairosvg": "cairosvg", "PIL": "pillow"}
    missing = [pkg for mod, pkg in required.items() if importlib.util.find_spec(mod) is None]
    if missing:
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        answer = messagebox.askyesno(
            "Dipendenze mancanti",
            f"Mancano le seguenti librerie Python necessarie:\n• {', '.join(missing)}\n\n"
            "Vuoi installarle automaticamente adesso?",
        )
        if not answer:
            root_tmp.destroy()
            return False
        try:
            cmd = [sys.executable, "-m", "pip", "install", *missing]
            if os.name != "nt":
                cmd.extend(["--user", "--break-system-packages"])
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Errore installazione", f"Impossibile installare le dipendenze:\n{exc}")
            root_tmp.destroy()
            return False
        root_tmp.destroy()
    try:
        import cairosvg  # noqa: F401
    except OSError:
        root_tmp = tk.Tk()
        root_tmp.withdraw()
        if os.name == "nt":
            answer = messagebox.askyesno(
                "Runtime Cairo mancante (Windows)",
                "CairoSVG richiede la libreria nativa GTK/Cairo su Windows (libcairo-2.dll).\n\n"
                "Vuoi provare a installarla automaticamente tramite winget?",
            )
            if answer:
                try:
                    subprocess.check_call(["winget", "install", "-e", "--id", "tschoonj.GTKForWindows"])
                    messagebox.showinfo("Installazione completata", "Runtime GTK/Cairo installato. Riavvia lo script.")
                except Exception as exc:
                    messagebox.showerror("Errore winget", f"Installazione non riuscita:\n{exc}")
        else:
            messagebox.showerror(
                "Libreria di sistema mancante",
                "Installa 'libcairo2' tramite il gestore pacchetti (es. sudo apt install libcairo2).",
            )
        root_tmp.destroy()
        return False
    return True
if not ensure_dependencies():
    sys.exit(1)
import cairosvg
from PIL import Image
class SVG2ICOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG to Windows ICO Converter")
        self.root.geometry("520x330")
        self.root.resizable(False, False)
        main_frame = ttk.Frame(root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(main_frame, text="File SVG:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.svg_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.svg_var, width=42).grid(row=0, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_svg).grid(row=0, column=2, pady=5)
        ttk.Label(main_frame, text="Destinazione ICO:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dest_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.dest_var, width=42).grid(row=1, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_dest).grid(row=1, column=2, pady=5)
        self.transparent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame, 
            text="Sfondo esterno trasparente", 
            variable=self.transparent_var
        ).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=8)
        info_text = "Genera un'icona Windows (.ico) multi-risoluzione\n(16x16, 32x32, 48x48, 64x64, 128x128, 256x256) da SVG."
        ttk.Label(main_frame, text=info_text, foreground="#555555", justify=tk.LEFT).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        convert_btn = ttk.Button(main_frame, text="CONVERTI IN .ICO", command=self.convert)
        convert_btn.grid(row=4, column=0, columnspan=3, sticky="ew", pady=12)
        main_frame.columnconfigure(1, weight=1)
    def browse_svg(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona file SVG",
            filetypes=[("File SVG", "*.svg"), ("Tutti i file", "*.*")]
        )
        if filepath:
            self.svg_var.set(filepath)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            default_dest = os.path.join(os.path.dirname(filepath), f"{base_name}.ico")
            self.dest_var.set(default_dest)
    def browse_dest(self):
        svg_path = self.svg_var.get().strip()
        initial_file = "icon.ico"
        initial_dir = ""
        if svg_path and os.path.exists(svg_path):
            initial_dir = os.path.dirname(svg_path)
            initial_file = os.path.splitext(os.path.basename(svg_path))[0] + ".ico"
        filepath = filedialog.asksaveasfilename(
            title="Salva file ICO come",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".ico",
            filetypes=[("File ICO", "*.ico"), ("Tutti i file", "*.*")]
        )
        if filepath:
            self.dest_var.set(filepath)
    def convert(self):
        svg_path = self.svg_var.get().strip()
        dest_path = self.dest_var.get().strip()
        transparent_bg = self.transparent_var.get()
        if not svg_path or not os.path.isfile(svg_path):
            messagebox.showerror("Errore", "Seleziona un file SVG valido.")
            return
        if not dest_path:
            messagebox.showerror("Errore", "Seleziona un percorso di destinazione per il file ICO.")
            return
        try:
            svg_bytes = open(svg_path, "rb").read()
            if transparent_bg:
                ET.register_namespace("", "http://w3.org")
                root_xml = ET.fromstring(svg_bytes)
                for child in list(root_xml):
                    tag_name = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                    if tag_name == "rect":
                        w = child.attrib.get("width", "")
                        h = child.attrib.get("height", "")
                        x = float(child.attrib.get("x", "0").replace("px", "") or 0)
                        y = float(child.attrib.get("y", "0").replace("px", "") or 0)
                        if x <= 0 and y <= 0 and (w.endswith("%") or h.endswith("%") or w in ("512", "100") or h in ("512", "100")):
                            root_xml.remove(child)
                            break
                svg_bytes = ET.tostring(root_xml, encoding="utf-8", xml_declaration=True)
            png_bytes = cairosvg.svg2png(bytestring=svg_bytes, output_width=512, output_height=512)
            img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(dest_path, format="ICO", sizes=sizes)
            messagebox.showinfo("Completato", f"Icona Windows ICO generata con successo in:\n{dest_path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la conversione:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SVG2ICOApp(root)
    root.mainloop()
