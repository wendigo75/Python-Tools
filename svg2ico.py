# ==============================================================================
# SVG to Android Icons Converter
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

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz  # PyMuPDF
from PIL import Image

class SVG2ICOApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG to Windows ICO Converter")
        self.root.geometry("520x330")
        self.root.resizable(False, False)

        main_frame = ttk.Frame(root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # SVG File selection
        ttk.Label(main_frame, text="File SVG:", font=("Segoe UI", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.svg_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.svg_var, width=42).grid(row=0, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_svg).grid(row=0, column=2, pady=5)

        # Output .ico destination
        ttk.Label(main_frame, text="Destinazione ICO:", font=("Segoe UI", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dest_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.dest_var, width=42).grid(row=1, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_dest).grid(row=1, column=2, pady=5)

        # Transparent background checkbox (like svg_to_android_icons.py)
        self.transparent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame, 
            text="Sfondo esterno trasparente (deseleziona per sfondo bianco)", 
            variable=self.transparent_var
        ).grid(row=2, column=0, columnspan=3, sticky=tk.W, pady=8)

        # Info label / description
        info_text = "Genera un'icona Windows (.ico) multi-risoluzione\n(16x16, 32x32, 48x48, 64x64, 128x128, 256x256) da SVG."
        ttk.Label(main_frame, text=info_text, foreground="#555555", justify=tk.LEFT).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)

        # Convert button
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
            doc = fitz.open(svg_path)
            page = doc[0]
            zoom = 4.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=True)
            img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)

            # Se transparent_bg è True, mantiene la trasparenza nativa.
            # Se è False, mantiene lo sfondo originale così come disegnato nell'SVG senza forzare il bianco.
            img = img.convert("RGBA")

            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
            img.save(dest_path, format="ICO", sizes=sizes)

            messagebox.showinfo("Completato", f"Icona Windows ICO generata con successo in:\n{dest_path}")
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la conversione:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SVG2ICOApp(root)
    root.mainloop()

