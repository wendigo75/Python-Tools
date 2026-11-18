#!/usr/bin/env python3
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
    vettoriali interni nel documento principale.
    """
    base_dir = os.path.dirname(os.path.abspath(svg_path))
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    parent_map = {child: parent for parent in root.iter() for child in parent}
    for elem in list(root.iter()):
        tag_name = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag_name != "image":
            continue
        href = (
            elem.attrib.get("href")
            or elem.attrib.get("{http://www.w3.org/2000/svg}href")
            or elem.attrib.get("{http://www.w3.org/1999/xlink}href")
        )
        if not href or href.startswith("data:") or href.startswith("http"):
            continue
        ext_path = os.path.join(base_dir, href)
        if not os.path.isfile(ext_path) or not ext_path.lower().endswith(".svg"):
            continue
        x = float(elem.attrib.get("x", "0").replace("px", ""))
        y = float(elem.attrib.get("y", "0").replace("px", ""))
        w_str = elem.attrib.get("width", "")
        h_str = elem.attrib.get("height", "")
        ext_tree = ET.parse(ext_path)
        ext_root = ext_tree.getroot()
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
        g = ET.Element("{http://www.w3.org/2000/svg}g")
        transform = f"translate({x}, {y}) scale({scale_x}, {scale_y})"
        if vb_x != 0 or vb_y != 0:
            transform += f" translate({-vb_x}, {-vb_y})"
        g.set("transform", transform)
        if "opacity" in elem.attrib:
            g.set("opacity", elem.attrib["opacity"])
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
    merged_svg_bytes = inline_nested_svgs(svg_path)
    png_bytes = cairosvg.svg2png(
        bytestring=merged_svg_bytes,
        output_width=width,
        output_height=height,
    )
    temp_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    if transparent_bg:
        temp_img.save(out_path, "PNG")
    else:
        white_bg = Image.new("RGBA", temp_img.size, (255, 255, 255, 255))
        final_img = Image.alpha_composite(white_bg, temp_img).convert("RGB")
        final_img.save(out_path, "PNG")
def create_adaptive_foreground(svg_path, out_path, transparent_bg=True):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    merged_svg_bytes = inline_nested_svgs(svg_path)
    canvas_size = 432
    icon_size = 264
    png_bytes = cairosvg.svg2png(
        bytestring=merged_svg_bytes,
        output_width=icon_size,
        output_height=icon_size,
    )
    icon_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0) if transparent_bg else (255, 255, 255, 255))
    offset = (canvas_size - icon_size) // 2
    canvas.paste(icon_img, (offset, offset), icon_img)
    canvas.save(out_path, "PNG")
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
        ttk.Label(main_frame, text="SVG:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.svg_var, width=42).grid(row=0, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_svg).grid(row=0, column=2, pady=5)
        ttk.Label(main_frame, text="Dest:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.dest_var, width=42).grid(row=1, column=1, padx=6, pady=5, sticky="ew")
        ttk.Button(main_frame, text="...", width=4, command=self.browse_dest).grid(row=1, column=2, pady=5)
        ttk.Label(main_frame, text="Nome:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(main_frame, textvariable=self.name_var, width=22).grid(row=2, column=1, padx=6, pady=5, sticky="W")
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
        ttk.Checkbutton(
            main_frame,
            text="Sfondo esterno trasparente",
            variable=self.transp_var,
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=6)
        ttk.Label(
            main_frame,
            text="Motore: CairoSVG + XML SVG Merger (Pronto)",
            foreground="green",
        ).grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=4)
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
                fg_file = os.path.join(dest_dir, f"{name}_foreground.png")
                create_adaptive_foreground(svg_path, fg_file, transparent_bg)    
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
