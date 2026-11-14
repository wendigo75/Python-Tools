# ==============================================================================
# Image Vectorizer (Raster to SVG)
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
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image
import vtracer


class IMG2SVGApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Image to SVG Vector Converter")
        self.root.geometry("520x350")
        self.root.resizable(False, False)

        main_frame = ttk.Frame(root, padding=12)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Selezione file immagine
        ttk.Label(main_frame, text="File Immagine:", font=("Segoe UI", 9, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.img_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.img_var, width=42).grid(
            row=0, column=1, padx=6, pady=5, sticky="ew"
        )
        ttk.Button(main_frame, text="...", width=4, command=self.browse_img).grid(
            row=0, column=2, pady=5
        )

        # Destinazione file .svg
        ttk.Label(main_frame, text="Destinazione SVG:", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.dest_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.dest_var, width=42).grid(
            row=1, column=1, padx=6, pady=5, sticky="ew"
        )
        ttk.Button(main_frame, text="...", width=4, command=self.browse_dest).grid(
            row=1, column=2, pady=5
        )

        # Modalità colore o bianco/nero
        ttk.Label(main_frame, text="Modalità:", font=("Segoe UI", 9, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.colormode_var = tk.StringVar(value="color")
        mode_frame = ttk.Frame(main_frame)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=6, pady=5)
        ttk.Radiobutton(
            mode_frame, text="A colori", variable=self.colormode_var, value="color"
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Radiobutton(
            mode_frame, text="Bianco e Nero (Binary)", variable=self.colormode_var, value="binary"
        ).pack(side=tk.LEFT)

        # Checkbox rimozione sfondo bianco
        self.remove_white_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            main_frame,
            text="Rendi trasparente lo sfondo bianco puro",
            variable=self.remove_white_var,
        ).grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=6)

        # Descrizione
        info_text = (
            "Vettorializza immagini raster (PNG, JPG, WEBP, BMP, ICO)\n"
            "in tracciati SVG scalabili."
        )
        ttk.Label(main_frame, text=info_text, foreground="#555555", justify=tk.LEFT).grid(
            row=4, column=0, columnspan=3, sticky=tk.W, pady=5
        )

        # Pulsante Converti
        convert_btn = ttk.Button(main_frame, text="CONVERTI IN .SVG", command=self.convert)
        convert_btn.grid(row=5, column=0, columnspan=3, sticky="ew", pady=12)

        main_frame.columnconfigure(1, weight=1)

    def browse_img(self):
        filepath = filedialog.askopenfilename(
            title="Seleziona immagine",
            filetypes=[
                ("Immagini supportate", "*.png *.jpg *.jpeg *.webp *.bmp *.gif *.ico"),
                ("Tutti i file", "*.*"),
            ],
        )
        if filepath:
            self.img_var.set(filepath)
            base_name = os.path.splitext(os.path.basename(filepath))[0]
            default_dest = os.path.join(os.path.dirname(filepath), f"{base_name}.svg")
            self.dest_var.set(default_dest)

    def browse_dest(self):
        img_path = self.img_var.get().strip()
        initial_file = "output.svg"
        initial_dir = ""

        if img_path and os.path.exists(img_path):
            initial_dir = os.path.dirname(img_path)
            initial_file = os.path.splitext(os.path.basename(img_path))[0] + ".svg"

        filepath = filedialog.asksaveasfilename(
            title="Salva file SVG come",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".svg",
            filetypes=[("File SVG", "*.svg"), ("Tutti i file", "*.*")],
        )
        if filepath:
            self.dest_var.set(filepath)

    def convert(self):
        img_path = self.img_var.get().strip()
        dest_path = self.dest_var.get().strip()
        colormode = self.colormode_var.get()
        remove_white = self.remove_white_var.get()

        if not img_path or not os.path.isfile(img_path):
            messagebox.showerror("Errore", "Seleziona un file immagine valido.")
            return

        if not dest_path:
            messagebox.showerror("Errore", "Seleziona un percorso di destinazione per il file SVG.")
            return

        tmp_png = None
        try:
            img = Image.open(img_path).convert("RGBA")

            if remove_white:
                pixels = img.getdata()
                new_pixels = [
                    (255, 255, 255, 0) if (r > 245 and g > 245 and b > 245) else (r, g, b, a)
                    for (r, g, b, a) in pixels
                ]
                img.putdata(new_pixels)

            fd, tmp_png = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            img.save(tmp_png, format="PNG")

            vtracer.convert_image_to_svg_py(
                tmp_png,
                dest_path,
                colormode=colormode,
                hierarchical="stacked",
                mode="spline",
                filter_speckle=4,
                color_precision=6,
                layer_difference=16,
                corner_threshold=60,
                length_threshold=4.0,
                max_iterations=10,
                splice_threshold=45,
                path_precision=3,
            )

            messagebox.showinfo(
                "Completato", f"File SVG vettoriale generato con successo in:\n{dest_path}"
            )
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la conversione:\n{str(e)}")
        finally:
            if tmp_png and os.path.exists(tmp_png):
                os.remove(tmp_png)


if __name__ == "__main__":
    root = tk.Tk()
    app = IMG2SVGApp(root)
    root.mainloop()
