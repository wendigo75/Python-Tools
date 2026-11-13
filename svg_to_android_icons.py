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
import re
import tkinter as tk
import xml.etree.ElementTree as ET
from tkinter import filedialog, messagebox, ttk

import fitz  # PyMuPDF
from PIL import Image

DENSITIES = {
    "mdpi": 48,
    "hdpi": 72,
    "xhdpi": 96,
    "xxhdpi": 144,
    "xxxhdpi": 192,
}


def inline_nested_svgs(svg_path):
    """
    Sostituisce i tag <image href="altro.svg"> inserendo direttamente i tracciati
    vettoriali interni nel documento principale, aggirando il limite di PyMuPDF.
    """
    base_dir = os.path.dirname(os.path.abspath(svg_path))
    ET.register_namespace("", "http://w3.org")
    ET.register_namespace("xlink", "http://w3.org")

    tree = ET.parse(svg_path)
    root = tree.getroot()

    # Mappa dei padri per poter sostituire i nodi <image>
    parent_map = {child: parent for parent in root.iter() for child in parent}

    for elem in list(root.iter()):
        tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag_name != "image":
            continue

        href = (
            elem.attrib.get("href")
            or elem.attrib.get("{http://w3.org}href")
        )
        if not href or href.startswith("data:") or href.startswith("http"):
            continue

        ext_path = os.path.join(base_dir, href)
        if not os.path.isfile(ext_path) or not ext_path.lower().endswith(".svg"):
            continue

        # Leggi dimensioni e posizione dell'immagine collegata
        x = float(elem.attrib.get("x", "0").replace("px", ""))
        y = float(elem.attrib.get("y", "0").replace("px", ""))
        w_str = elem.attrib.get("width", "")
        h_str = elem.attrib.get("height", "")

        ext_tree = ET.parse(ext_path)
        ext_root = ext_tree.getroot()

        # Calcola il viewBox dell'SVG esterno per scalarlo correttamente
        vb = ext_root.attrib.get("viewBox")
        if vb:
            parts = [float(v) for v in re.split(r"[\s,]+", vb.strip())]
            vb_x, vb_y, vb_w, vb_h = parts[0], parts[1], parts[2], parts[3]
        else:
            vb_x, vb_y = 0.0, 0.0
            vb_w = float(ext_root.attrib.get("width", "100").replace("px", ""))
            vb_h = float(ext_root.attrib.get("height", "100").replace("px", ""))

        target_w = float(w_str.replace("px", "")) if w_str else vb_w
        target_h = float(h_str.replace("px", "")) if h_str else vb_h

        scale_x = target_w / vb_w if vb_w else 1.0
        scale_y = target_h / vb_h if vb_h else 1.0

        # Crea un gruppo <g> posizionato e scalato al posto di <image>
        g = ET.Element("{http://w3.org}g")
        transform = f"translate({x}, {y}) scale({scale_x}, {scale_y})"
        if vb_x != 0 or vb_y != 0:
            transform += f" translate({-vb_x}, {-vb_y})"
        g.set("transform", transform)

        if "opacity" in elem.attrib:
            g.set("opacity", elem.attrib["opacity"])

        # Copia tutti gli elementi interni (path, circle, rect, g, defs, ecc.)
        for child in list(ext_root):
            g.append(child)

        parent = parent_map.get(elem)
        if parent is not None:
            idx = list(parent).index(elem)
            parent.remove(elem)
            parent.insert(idx, g)

    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def convert_svg_to_png(svg_path, out_path, width, height, transparent_bg=True):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    # Fonde eventuali SVG esterni (es. yenten-mark.svg) nei tracciati principali
    merged_svg_bytes = inline_nested_svgs(svg_path)

    doc = fitz.open(stream=merged_svg_bytes, filetype="svg")
    page = doc[0]

    zoom_x = width / page.rect.width
    zoom_y = height / page.rect.height
    matrix = fitz.Matrix(zoom_x, zoom_y)

    pix = page.get_pixmap(matrix=matrix, alpha=True)
    doc.close()

    if transparent_bg:
        pix.save(out_path)
    else:
        temp_img = Image.frombytes("RGBA", [pix.width, pix.height], pix.samples)
        white_bg = Image.new("RGBA", temp_img.size, (255, 255, 255, 255))
        final_img = Image.alpha_composite(white_bg, temp_img).convert("RGB")
        final_img.save(out_path, "PNG")


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("SVG to Android Icons")
        self.root.geometry("480x310")
        self.root.resizable(False, False)

        self.svg_var = tk.StringVar()
        self.dest_var = tk.StringVar()
        self.name_var = tk.StringVar(value="ic_launcher")
        self.mode_var = tk.StringVar(value="set")
        self.size_var = tk.StringVar(value="512")
        self.transp_var = tk.BooleanVar(value=True)

        main_frame = ttk.Frame(root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Riga 0: File SVG
        ttk.Label(main_frame, text="SVG:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.svg_var, width=42).grid(row=0, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_svg).grid(row=0, column=2, pady=5)

        # Riga 1: Cartella Destinazione
        ttk.Label(main_frame, text="Dest:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.dest_var, width=42).grid(row=1, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_dest).grid(row=1, column=2, pady=5)

        # Riga 2: Nome file output
        ttk.Label(main_frame, text="Nome:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.name_var, width=22).grid(row=2, column=1, padx=6, pady=5, sticky="W")

        # Riga 3: Modalità
        ttk.Label(main_frame, text="Modo:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky=tk.NW, pady=8)
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=6, pady=4)

        ttk.Radiobutton(
            mode_frame,
            text="Set Android completo (nella stessa cartella)",
            variable=self.mode_var,
            value="set",
            command=self.toggle_spinbox,
        ).pack(anchor=tk.W, pady=2)

        single_frame = ttk.Frame(mode_frame)
        single_frame.pack(anchor=tk.W, pady=2)

        ttk.Radiobutton(
            single_frame,
            text="Singolo PNG (px):",
            variable=self.mode_var,
            value="single",
            command=self.toggle_spinbox,
        ).pack(side=tk.LEFT)

        self.spinbox = ttk.Spinbox(
            single_frame,
            from_=16,
            to=4096,
            textvariable=self.size_var,
            width=6,
            state=tk.DISABLED,
        )
        self.spinbox.pack(side=tk.LEFT, padx=6)

        # Riga 4: Spunta Sfondo Trasparente
        ttk.Checkbutton(
            main_frame,
            text="Sfondo esterno trasparente (deseleziona per sfondo bianco)",
            variable=self.transp_var,
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=6)

        # Riga 5: Stato Libreria
        ttk.Label(
            main_frame,
            text="Motore: PyMuPDF + XML SVG Merger (Pronto)",
            foreground="green",
        ).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=4)

        # Riga 6: Pulsante Converti
        ttk.Button(main_frame, text="CONVERTI", command=self.convert).grid(
            row=6, column=0, columnspan=3, pady=8, sticky="ew"
        )

        main_frame.columnconfigure(1, weight=1)

    def toggle_spinbox(self):
        if self.mode_var.get() == "single":
            self.spinbox.config(state=tk.NORMAL)
        else:
            self.spinbox.config(state=tk.DISABLED)

    def browse_svg(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona file SVG",
            filetypes=[("File SVG", "*.svg"), ("Tutti i file", "*.*")],
        )
        if filepath:
            self.svg_var.set(filepath)
            if not self.dest_var.get():
                self.dest_var.set(os.path.dirname(filepath))
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            self.name_var.set(base_name)

    def browse_dest(self):
        folder = filedialog.askdirectory(title="Seleziona cartella di destinazione")
        if folder:
            self.dest_var.set(folder)

    def convert(self):
        svg_path = self.svg_var.get().strip()
        dest_dir = self.dest_var.get().strip()
        mode = self.mode_var.get()
        name = self.name_var.get().strip() or "ic_launcher"
        transparent_bg = self.transp_var.get()

        if not svg_path or not os.path.isfile(svg_path):
            messagebox.showerror("Errore", "Seleziona un file SVG valido.")
            return

        if not dest_dir:
            messagebox.showerror("Errore", "Seleziona una cartella di destinazione.")
            return

        try:
            if mode == "set":
                for density_name, size in DENSITIES.items():
                    out_file = os.path.join(dest_dir, f"{name}_{density_name}.png")
                    convert_svg_to_png(svg_path, out_file, size, size, transparent_bg)
                messagebox.showinfo(
                    "Completato",
                    f"Set Android creato direttamente in:\n{dest_dir}",
                )
            else:
                size = int(self.size_var.get())
                out_file = os.path.join(dest_dir, f"{name}_{size}x{size}.png")
                convert_svg_to_png(svg_path, out_file, size, size, transparent_bg)
                messagebox.showinfo("Completato", f"Immagine PNG salvata in:\n{out_file}")
        except Exception as e:
            messagebox.showerror("Errore durante la conversione", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
