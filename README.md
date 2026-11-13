# Python-Tools

A collection of lightweight, standalone Python utility scripts with minimal GUIs to speed up everyday development tasks.

---

## 📂 Tools Index

| Script | Description | Dependencies |
| :--- | :--- | :--- |
| [`svg_to_android_icons.py`](#1-svg_to_android_icons) | Converts `.svg` files into a complete set of Android PNG icons (`mdpi` to `xxxhdpi`) or custom-sized PNGs. | `pymupdf`, `pillow` |

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


## 📄 License
This repository is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

