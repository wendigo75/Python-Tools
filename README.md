# Python-Tools

A collection of lightweight, standalone Python utility scripts with minimal GUIs to speed up everyday development tasks.

---

## 📂 Tools Index

| Script | Description | Dependencies |
| :--- | :--- | :--- |
| [`svg_to_android_icons.py`](#1-svg_to_android_icons) | Converts `.svg` files into a complete set of Android PNG icons (`mdpi` to `xxxhdpi`) or custom-sized PNGs. | `pymupdf`, `pillow` |
| [`svg2ico.py`](#2-svg2ico) | Converts `.svg` files into multi-resolution Windows `.ico` icons (`16x16` up to `256x256`). | `pymupdf`, `pillow` |
| [`img2svg.py`](#3-img2svg) | **Image Vectorizer** — Traces and vectorizes raster images into scalable `.svg` files. | `pillow`, `vtracer` |
| [`desktop_shortcut_manager.py`](#4-desktop_shortcut_manager) | **Linux `.desktop` Shortcut Manager** — Creates or removes Freedesktop `.desktop` shortcuts and system icons. | `None` (Standard Library) |

---

## 🛠️ Tool Details

### 1. `svg_to_android_icons.py`
A minimal Tkinter GUI tool to convert vector `.svg` files into high-quality `.png` icons without external browser dependencies.

* **Key Features:**
  * Generates the full Android icon set (`mdpi` 48px, `hdpi` 72px, `xhdpi` 96px, `xxhdpi` 144px, `xxxhdpi` 192px) directly into the target folder.
  * Supports single custom-resolution PNG export (from 16px up to 4096px).
  * Automatically merges nested/external `.svg` files referenced inside the main SVG.
  * Toggle between transparent outer background or solid white background.
* **Install & Run:**
  ```bash
  pip install pymupdf pillow
  python svg_to_android_icons.py
  ```

---

### 2. `svg2ico.py`
A minimal Tkinter GUI tool to convert vector `.svg` files into multi-resolution Windows `.ico` files.

* **Key Features:**
  * Generates a single `.ico` file containing 6 standard Windows icon sizes (`16x16`, `32x32`, `48x48`, `64x64`, `128x128`, `256x256`).
  * Automatically suggests the output path and filename based on the selected `.svg` file.
  * Preserves native transparency or keeps the original SVG background intact.
* **Install & Run:**
  ```bash
  pip install pymupdf pillow
  python svg2ico.py
  ```

---

### 3. `img2svg.py` (Image Vectorizer)
A minimal Tkinter GUI tool to trace and vectorize raster images into scalable `.svg` vector files.

* **Key Features:**
  * Supports multiple raster input formats (`PNG`, `JPG`, `JPEG`, `WEBP`, `BMP`, `GIF`, `ICO`).
  * Converts images into true vector `<path>` curves using either full-color or black-and-white (`Binary`) tracing modes.
  * Optional toggle to automatically turn pure white backgrounds transparent before vectorizing.
  * Automatically suggests the output path and filename based on the selected image.
* **Install & Run:**
  ```bash
  pip install pillow vtracer
  python img2svg.py
  ```

  ---

### 4. `desktop_shortcut_manager.py` (Linux `.desktop` Shortcut Manager)
A minimal Tkinter GUI tool to register or remove standalone Linux executables in the desktop environment without manual file editing.

* **Key Features:**
  * Creates standard Freedesktop `.desktop` entries in `~/.local/share/applications/` and automatically places a trusted shortcut on the user's Desktop (`xdg-user-dir DESKTOP`).
  * Installs the selected `.svg` or `.png` icon into the local `hicolor` icon theme (`~/.local/share/icons/hicolor/`) and updates system icon/desktop caches.
  * Cleanly uninstalls all generated `.desktop` shortcuts and registered icons with a single click.
  * Uses only Python standard libraries (`tkinter`, `pathlib`, `shutil`, `subprocess`) with zero external dependencies.
* **Install & Run:**
  ```bash
  python3 desktop_shortcut_manager.py
  ```

---
  
## 📄 License
This repository is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

