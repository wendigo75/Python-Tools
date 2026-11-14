#!/usr/bin/env python3
# ==========================================================================
# Linux .desktop Shortcut Manager
# Copyright (c) 2026 wendigo75
# Licensed under the MIT License
# ==========================================================================

import re
import shutil
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

APPS_DIR = Path.home() / ".local" / "share" / "applications"
ICONS_BASE_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor"


def get_desktop_dir() -> Path:
    try:
        res = subprocess.run(
            ["xdg-user-dir", "DESKTOP"],
            capture_output=True,
            text=True,
            check=False,
        )
        out = res.stdout.strip()
        if out and Path(out).is_dir():
            return Path(out)
    except FileNotFoundError:
        pass

    for fallback in ("Desktop", "Scrivania"):
        candidate = Path.home() / fallback
        if candidate.is_dir():
            return candidate
    return Path.home() / "Desktop"


class DesktopShortcutManager:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Linux .desktop Shortcut Manager")
        self.root.geometry("540x185")
        self.root.resizable(False, False)

        self.exec_var = tk.StringVar()
        self.icon_var = tk.StringVar()

        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 10, "pady": 8}

        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        frame.columnconfigure(1, weight=1)

        # Row 1: Executable
        tk.Label(frame, text="Executable:", anchor="w").grid(
            row=0, column=0, sticky="w", **pad
        )
        tk.Entry(frame, textvariable=self.exec_var).grid(
            row=0, column=1, sticky="ew", **pad
        )
        tk.Button(frame, text="Browse...", width=10, command=self._browse_exec).grid(
            row=0, column=2, **pad
        )

        # Row 2: Icon
        tk.Label(frame, text="Icon (.svg/.png):", anchor="w").grid(
            row=1, column=0, sticky="w", **pad
        )
        tk.Entry(frame, textvariable=self.icon_var).grid(
            row=1, column=1, sticky="ew", **pad
        )
        tk.Button(frame, text="Browse...", width=10, command=self._browse_icon).grid(
            row=1, column=2, **pad
        )

        # Row 3: Action buttons (Uninstall left, Install right)
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=(14, 4))

        tk.Button(
            btn_frame,
            text="Uninstall (.desktop)",
            width=20,
            bg="#c62828",
            fg="white",
            command=self.uninstall_desktop,
        ).pack(side="left", padx=12)

        tk.Button(
            btn_frame,
            text="Install (.desktop)",
            width=20,
            bg="#2e7d32",
            fg="white",
            command=self.install_desktop,
        ).pack(side="left", padx=12)

    def _browse_exec(self) -> None:
        path = filedialog.askopenfilename(title="Select Executable File")
        if path:
            self.exec_var.set(path)

    def _browse_icon(self) -> None:
        path = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("Icon Files", "*.svg *.png"), ("All Files", "*.*")],
        )
        if path:
            self.icon_var.set(path)

    def _get_app_metadata(self, exec_path: Path) -> tuple[str, str, Path, Path]:
        stem = exec_path.stem
        display_name = (
            re.sub(r"(?<!^)(?=[A-Z])", " ", stem)
            .replace("_", " ")
            .replace("-", " ")
            .strip()
        )
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", stem).strip("_").lower()
        app_desktop = APPS_DIR / f"{slug}.desktop"
        user_desktop = get_desktop_dir() / f"{slug}.desktop"
        return display_name, slug, app_desktop, user_desktop

    def _get_icon_targets(self, slug: str) -> list[Path]:
        return [
            ICONS_BASE_DIR / "scalable" / "apps" / f"{slug}.svg",
            ICONS_BASE_DIR / "256x256" / "apps" / f"{slug}.png",
        ]

    def _trust_gnome_desktop_file(self, desktop_path: Path) -> None:
        try:
            subprocess.run(
                ["gio", "set", str(desktop_path), "metadata::trusted", "true"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except FileNotFoundError:
            pass

    def _refresh_caches(self) -> None:
        for cmd in (
            ["update-desktop-database", str(APPS_DIR)],
            ["gtk-update-icon-cache", "-f", "-t", str(ICONS_BASE_DIR)],
        ):
            try:
                subprocess.run(
                    cmd,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                pass

    def install_desktop(self) -> None:
        exec_raw = self.exec_var.get().strip()
        icon_raw = self.icon_var.get().strip()

        if not exec_raw:
            messagebox.showerror("Error", "Please select an executable file.")
            return

        exec_path = Path(exec_raw)
        if not exec_path.is_file():
            messagebox.showerror("Error", f"Executable not found:\n{exec_path}")
            return

        if not icon_raw:
            messagebox.showerror("Error", "Please select an icon file (.svg or .png).")
            return

        icon_path = Path(icon_raw)
        if not icon_path.is_file():
            messagebox.showerror("Error", f"Icon file not found:\n{icon_path}")
            return

        APPS_DIR.mkdir(parents=True, exist_ok=True)
        display_name, slug, app_desktop, user_desktop = self._get_app_metadata(exec_path)

        for old_icon in self._get_icon_targets(slug):
            if old_icon.exists():
                old_icon.unlink()

        ext = icon_path.suffix.lower()
        if ext == ".svg":
            dest_icon = ICONS_BASE_DIR / "scalable" / "apps" / f"{slug}.svg"
        else:
            dest_icon = ICONS_BASE_DIR / "256x256" / "apps" / f"{slug}.png"

        dest_icon.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon_path, dest_icon)

        content = (
            "[Desktop Entry]\n"
            "Version=1.0\n"
            "Type=Application\n"
            f"Name={display_name}\n"
            f'Exec="{exec_path.resolve()}"\n'
            f"Icon={slug}\n"
            "Terminal=false\n"
            "Categories=Utility;\n"
            f"StartupWMClass={exec_path.name}\n"
        )

        app_desktop.write_text(content, encoding="utf-8")
        app_desktop.chmod(0o755)

        if user_desktop.parent.is_dir():
            shutil.copy2(app_desktop, user_desktop)
            user_desktop.chmod(0o755)
            self._trust_gnome_desktop_file(user_desktop)

        self._refresh_caches()

        messagebox.showinfo(
            "Installed",
            f"Registered application shortcut and icon:\n"
            f"- Menu: {app_desktop}\n"
            f"- Desktop: {user_desktop}\n"
            f"- Icon: {dest_icon}",
        )

    def uninstall_desktop(self) -> None:
        exec_raw = self.exec_var.get().strip()
        if not exec_raw:
            messagebox.showerror("Error", "Please select the executable file to uninstall.")
            return

        _, slug, app_desktop, user_desktop = self._get_app_metadata(Path(exec_raw))
        removed = []

        for target in (app_desktop, user_desktop, *self._get_icon_targets(slug)):
            if target.exists():
                target.unlink()
                removed.append(str(target))

        if removed:
            self._refresh_caches()
            messagebox.showinfo(
                "Uninstalled",
                "Removed registered files:\n" + "\n".join(removed),
            )
        else:
            messagebox.showwarning(
                "Not Found", f"No registered files found for:\n{slug}"
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopShortcutManager(root)
    root.mainloop()

