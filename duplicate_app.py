import os
from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Optional

from PIL import Image, ImageTk

from duplicate_scanner import DuplicateFileManager, DuplicateGroup, DuplicateScanner

try:
    import winreg
except ImportError:
    winreg = None


class DuplicateApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Modular Duplicate File Cleaner")
        self.root.geometry("1050x650")

        self.scanner = DuplicateScanner()
        self.file_manager = DuplicateFileManager()
        self.duplicate_data: dict[str, DuplicateGroup] = {}
        self.checked_paths: set[Path] = set()
        self.current_preview_image = None
        self.is_dark_mode = self.detect_system_dark_mode()
        self.theme_colors = {}
        self.view_filter = "all"
        self.delete_all_var = tk.BooleanVar(value=False)
        self.show_original_var = tk.BooleanVar(value=False)
        self.show_duplicate_var = tk.BooleanVar(value=False)

        self.setup_styles()
        self.create_widgets()
        self.apply_theme()

    def setup_styles(self) -> None:
        self.style = ttk.Style()
        self.style.theme_use("clam")

    @staticmethod
    def detect_system_dark_mode() -> bool:
        if sys.platform != "win32" or winreg is None:
            return False
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            ) as key:
                light_theme, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return light_theme == 0
        except (FileNotFoundError, OSError):
            return False

    def apply_theme(self) -> None:
        if self.is_dark_mode:
            colors = {
                "background": "#202124",
                "foreground": "#f1f3f4",
                "field": "#303134",
                "selected": "#394b5f",
                "canvas": "#303134",
                "active": "#465d75",
                "disabled": "#7f8790",
                "muted": "#b8c0c8",
            }
        else:
            colors = {
                "background": "#f0f0f0",
                "foreground": "#202124",
                "field": "#ffffff",
                "selected": "#cfe2f3",
                "canvas": "#f0f0f0",
                "active": "#dbeafe",
                "disabled": "#888888",
                "muted": "#666666",
            }

        self.theme_colors = colors
        self.root.configure(bg=colors["background"])
        self.preview_canvas.configure(bg=colors["canvas"])
        self.style.configure(
            ".", background=colors["background"], foreground=colors["foreground"]
        )
        self.style.configure(
            "TFrame",
            background=colors["background"],
        )
        self.style.configure(
            "TLabel",
            background=colors["background"],
            foreground=colors["foreground"],
        )
        self.style.configure(
            "TLabelframe",
            background=colors["background"],
            foreground=colors["foreground"],
        )
        self.style.configure(
            "TLabelframe.Label",
            background=colors["background"],
            foreground=colors["foreground"],
        )
        self.style.configure(
            "TEntry",
            fieldbackground=colors["field"],
            foreground=colors["foreground"],
            insertcolor=colors["foreground"],
            selectbackground=colors["selected"],
            selectforeground=colors["foreground"],
        )
        self.style.map(
            "TEntry",
            fieldbackground=[
                ("disabled", colors["background"]),
                ("readonly", colors["field"]),
            ],
            foreground=[("disabled", colors["disabled"])],
        )
        self.style.configure(
            "Treeview",
            background=colors["field"],
            fieldbackground=colors["field"],
            foreground=colors["foreground"],
            selectbackground=colors["selected"],
            selectforeground=colors["foreground"],
        )
        self.style.map(
            "Treeview",
            background=[("selected", colors["selected"])],
            foreground=[("selected", colors["foreground"])],
        )
        self.style.configure(
            "TButton",
            background=colors["field"],
            foreground=colors["foreground"],
        )
        self.style.map(
            "TButton",
            background=[
                ("disabled", colors["background"]),
                ("pressed", colors["selected"]),
                ("active", colors["active"]),
            ],
            foreground=[
                ("disabled", colors["disabled"]),
                ("pressed", colors["foreground"]),
                ("active", colors["foreground"]),
            ],
        )
        self.style.configure(
            "TCheckbutton",
            background=colors["background"],
            foreground=colors["foreground"],
        )
        self.style.map(
            "TCheckbutton",
            background=[
                ("disabled", colors["background"]),
                ("active", colors["active"]),
            ],
            foreground=[
                ("disabled", colors["disabled"]),
                ("active", colors["foreground"]),
            ],
        )
        self.style.configure(
            "TScrollbar",
            background=colors["field"],
            troughcolor=colors["background"],
            arrowcolor=colors["foreground"],
        )
        self.style.configure(
            "TPanedwindow",
            background=colors["background"],
        )
        self.tree.tag_configure("original", foreground=colors["foreground"])
        self.tree.tag_configure(
            "duplicate",
            foreground="#ff6b6b" if self.is_dark_mode else "#c62828",
        )
        self.theme_btn.config(
            text="Switch to Light Mode" if self.is_dark_mode else "Switch to Dark Mode"
        )

    def create_widgets(self) -> None:
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(top_frame, text="Target Folder:", font=("Segoe UI", 10, "bold")).pack(
            side=tk.LEFT, padx=5
        )
        self.path_entry = ttk.Entry(top_frame, width=65)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(
            top_frame, text="Browse", command=self.browse_folder, cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top_frame,
            text="Scan for Duplicates",
            command=self.run_scan,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            top_frame,
            text="Recheck Folder",
            command=self.recheck_folder,
            cursor="hand2",
        ).pack(side=tk.LEFT, padx=5)
        self.theme_btn = ttk.Button(
            top_frame, text="Switch Theme", command=self.toggle_theme, cursor="hand2"
        )
        self.theme_btn.pack(side=tk.LEFT, padx=5)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)
        self.tree = ttk.Treeview(
            left_frame,
            columns=("checked", "path", "file_type"),
            selectmode="extended",
        )
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.heading(
            "#0", text="Duplicates Tree (Format, Size, Dimensions matched)", anchor=tk.W
        )
        self.tree.heading("checked", text="Delete", anchor=tk.CENTER)
        self.tree.heading("path", text="Path", anchor=tk.W)
        self.tree.heading("file_type", text="Status", anchor=tk.W)
        self.tree.column("checked", width=55, minwidth=55, stretch=False, anchor=tk.CENTER)
        self.tree.column("path", width=0, minwidth=0, stretch=False)
        self.tree.column("file_type", width=95, minwidth=95, stretch=False)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)
        self.tree.bind("<Button-1>", self.on_tree_click)
        self.tree.bind("<Double-1>", self.open_selected_file)
        self.tree.bind("<Button-3>", self.show_context_menu)
        self.tree.bind("<Motion>", self.update_tree_cursor)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        right_frame = ttk.LabelFrame(main_pane, text=" File Preview & Details ", padding=10)
        main_pane.add(right_frame, weight=2)
        self.details_label = ttk.Label(
            right_frame,
            text="Select a file to view details.",
            font=("Segoe UI", 9),
            wraplength=350,
        )
        self.details_label.pack(anchor=tk.W, pady=5)
        self.preview_canvas = tk.Canvas(
            right_frame, bg="#f0f0f0", width=320, height=320
        )
        self.preview_canvas.pack(pady=10)
        self.reset_preview()

        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)
        options_frame = ttk.Frame(self.root, padding=(10, 0, 10, 5))
        options_frame.pack(fill=tk.X, side=tk.BOTTOM)
        ttk.Checkbutton(
            options_frame,
            text="Delete all duplicates",
            variable=self.delete_all_var,
            command=self.toggle_select_all_duplicates,
        ).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(
            options_frame,
            text="Show all original",
            variable=self.show_original_var,
            command=lambda: self.set_view_filter("original"),
        ).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(
            options_frame,
            text="Show all duplicates",
            variable=self.show_duplicate_var,
            command=lambda: self.set_view_filter("duplicate"),
        ).pack(side=tk.LEFT, padx=5)
        self.delete_btn = ttk.Button(
            bottom_frame,
            text="Delete All Selected",
            command=self.delete_checked_duplicates,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        self.delete_all_btn = ttk.Button(
            bottom_frame,
            text="Delete All Duplicates",
            command=self.delete_all_duplicates,
            state=tk.DISABLED,
            cursor="hand2",
        )
        self.delete_all_btn.pack(side=tk.RIGHT, padx=5)

    def toggle_theme(self) -> None:
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def browse_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def run_scan(self) -> None:
        self.scan_folder("Scan Complete")

    def recheck_folder(self) -> None:
        self.scan_folder("Recheck Complete")

    def scan_folder(self, result_title: str) -> None:
        target_dir = self.path_entry.get().strip()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        self.clear_tree()
        self.checked_paths.clear()
        self.duplicate_data = self.scanner.scan_directory(target_dir)
        if not self.duplicate_data:
            self.update_delete_buttons()
            messagebox.showinfo("Result", "No duplicate files found matching your criteria!")
            return

        self.populate_tree()
        self.update_delete_buttons()
        messagebox.showinfo(
            result_title, f"Found {len(self.duplicate_data)} duplicate groups!"
        )

    def populate_tree(self) -> None:
        for group_name, group in self.duplicate_data.items():
            visible_files = []
            if self.view_filter in ("all", "original"):
                visible_files.append((group.original, "original"))
            if self.view_filter in ("all", "duplicate"):
                visible_files.extend(
                    (duplicate, "duplicate") for duplicate in group.duplicates
                )
            if not visible_files:
                continue

            group_text = (
                f"{group_name} | Ext: {group.extension} | "
                f"Size: {group.size:,} bytes | Dims: {group.dimensions or 'N/A'}"
            )
            parent_node = self.tree.insert("", tk.END, text=group_text, open=True)
            for path, file_type in visible_files:
                label = "[KEEP ORIGINAL]" if file_type == "original" else "[DUPLICATE]"
                self.tree.insert(
                    parent_node,
                    tk.END,
                    text=f"{label} {path.name}",
                    values=(self.checkbox_text(path), str(path), file_type),
                    tags=(file_type,),
                )

    def clear_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def checkbox_text(self, path: Path) -> str:
        return "[x]" if path in self.checked_paths else "[ ]"

    def on_tree_click(self, event) -> Optional[str]:
        item = self.tree.identify_row(event.y)
        if item and self.tree.identify_column(event.x) == "#1":
            self.toggle_checked(item)
            return "break"
        return None

    def update_tree_cursor(self, event) -> None:
        item = self.tree.identify_row(event.y)
        is_file_name = (
            bool(item)
            and bool(self.tree.item(item, "values"))
            and self.tree.identify_column(event.x) == "#0"
        )
        self.tree.configure(cursor="hand2" if is_file_name else "")

    def toggle_checked(self, item: str) -> None:
        values = self.tree.item(item, "values")
        if not values:
            return
        path = Path(values[1])
        if path in self.checked_paths:
            self.checked_paths.remove(path)
        else:
            self.checked_paths.add(path)
        self.tree.set(item, "checked", self.checkbox_text(path))
        self.update_delete_buttons()

    def on_select_item(self, _event) -> None:
        selected_items = self.tree.selection()
        file_items = [
            item for item in selected_items if self.tree.item(item, "values")
        ]
        if len(file_items) == 1:
            values = self.tree.item(file_items[0], "values")
            self.load_file_details(values[1], values[2])
        elif len(file_items) > 1:
            self.details_label.config(text=f"{len(file_items)} files selected.")
            self.delete_btn.config(state=tk.DISABLED)

    def load_file_details(self, file_path: str, file_type: str) -> None:
        path_obj = Path(file_path)
        if not path_obj.is_file():
            return

        size = path_obj.stat().st_size
        dimensions = self.scanner.get_image_dimensions(path_obj)
        self.details_label.config(
            text=(
                f"File Name: {path_obj.name}\nPath: {file_path}\n"
                f"Type: {'Original (Safe)' if file_type == 'original' else 'Duplicate'}\n"
                f"Size: {size:,} bytes\nDimensions: {dimensions or 'N/A'}"
            )
        )
        self.preview_canvas.delete("all")
        if path_obj.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}:
            self.preview_canvas.create_text(
                160,
                160,
                text="Preview available for images only",
                fill=self.theme_colors["muted"],
            )
            return
        try:
            with Image.open(path_obj) as image:
                image.thumbnail((300, 300))
                self.current_preview_image = ImageTk.PhotoImage(image.copy())
            self.preview_canvas.create_image(
                160, 160, image=self.current_preview_image, anchor=tk.CENTER
            )
        except (OSError, ValueError):
            self.preview_canvas.create_text(
                160, 160, text="Could not load preview", fill="red"
            )

    def get_checked_duplicate_paths(self) -> list[Path]:
        return [
            path
            for item in self.walk_file_items()
            for values in [self.tree.item(item, "values")]
            if values and values[2] == "duplicate"
            for path in [Path(values[1])]
            if path in self.checked_paths
        ]

    def walk_file_items(self) -> list[str]:
        return [
            child
            for parent in self.tree.get_children()
            for child in self.tree.get_children(parent)
        ]

    def delete_checked_duplicates(self) -> None:
        duplicate_paths = self.get_checked_duplicate_paths()
        if not duplicate_paths:
            messagebox.showinfo(
                "No Files Selected",
                "Check at least one duplicate file before deleting.",
            )
            return
        if messagebox.askyesno(
            "Confirm Deletion",
            f"Send {len(duplicate_paths)} checked duplicate file(s) to the Recycle Bin?",
        ):
            self.delete_paths(duplicate_paths)

    def toggle_select_all_duplicates(self) -> None:
        duplicate_paths = {
            duplicate
            for group in self.duplicate_data.values()
            for duplicate in group.duplicates
        }
        if self.delete_all_var.get():
            self.checked_paths.update(duplicate_paths)
        else:
            self.checked_paths.difference_update(duplicate_paths)
        self.refresh_tree()

    def set_view_filter(self, filter_name: str) -> None:
        if filter_name == "original" and self.show_original_var.get():
            self.show_duplicate_var.set(False)
            self.view_filter = "original"
        elif filter_name == "duplicate" and self.show_duplicate_var.get():
            self.show_original_var.set(False)
            self.view_filter = "duplicate"
        else:
            self.view_filter = "all"
        self.refresh_tree()

    def delete_all_duplicates(self) -> None:
        duplicate_paths = [
            duplicate
            for group in self.duplicate_data.values()
            for duplicate in group.duplicates
        ]
        if not duplicate_paths:
            self.update_delete_buttons()
            return
        if messagebox.askyesno(
            "Confirm Deletion",
            f"Send all {len(duplicate_paths)} duplicate files to the Recycle Bin?",
        ):
            self.delete_paths(duplicate_paths)

    def delete_paths(self, paths: list[Path]) -> None:
        deleted_paths = []
        failed_paths = []
        for path in paths:
            try:
                self.file_manager.move_to_recycle_bin(str(path))
                deleted_paths.append(path)
            except OSError:
                failed_paths.append(path)

        for path in deleted_paths:
            self.remove_file_from_data(path)
            self.checked_paths.discard(path)
        self.delete_all_var.set(False)
        self.refresh_tree()
        self.details_label.config(text="Select a file to view details.")
        self.reset_preview()

        if failed_paths:
            failed_names = ", ".join(path.name for path in failed_paths)
            messagebox.showerror(
                "Some Files Could Not Be Deleted",
                f"Moved {len(deleted_paths)} file(s) to the Recycle Bin.\n"
                f"Could not move: {failed_names}",
            )
        else:
            messagebox.showinfo(
                "Success",
                f"Moved {len(deleted_paths)} duplicate file(s) to the Recycle Bin.",
            )

    def remove_file_from_data(self, file_path: Path) -> None:
        for group_name, group in list(self.duplicate_data.items()):
            if group.original == file_path:
                if group.duplicates:
                    group.original = group.duplicates.pop(0)
                else:
                    del self.duplicate_data[group_name]
                return
            if file_path in group.duplicates:
                group.duplicates.remove(file_path)
                if not group.duplicates:
                    del self.duplicate_data[group_name]
                return

    def refresh_tree(self) -> None:
        self.clear_tree()
        self.populate_tree()
        self.update_delete_buttons()

    def update_delete_buttons(self) -> None:
        self.delete_all_btn.config(
            state=tk.NORMAL if self.duplicate_data else tk.DISABLED
        )
        self.delete_btn.config(
            state=tk.NORMAL if self.get_checked_duplicate_paths() else tk.DISABLED
        )

    def open_selected_file(self, event) -> None:
        item = self.tree.identify_row(event.y)
        values = self.tree.item(item, "values") if item else ()
        if values and self.tree.identify_column(event.x) == "#0":
            self.open_path(Path(values[1]))

    def open_path(self, path: Path) -> None:
        if not path.is_file():
            messagebox.showerror("Error", f"File does not exist:\n{path}")
            return
        try:
            os.startfile(str(path))
        except OSError as error:
            messagebox.showerror("Error", f"Could not open file: {error}")

    def open_containing_folder(self, path: Path) -> None:
        try:
            os.startfile(str(path.parent))
        except OSError as error:
            messagebox.showerror("Error", f"Could not open folder: {error}")

    def show_context_menu(self, event) -> str:
        item = self.tree.identify_row(event.y)
        values = self.tree.item(item, "values") if item else ()
        if not values:
            return "break"

        self.tree.selection_set(item)
        file_path = Path(values[1])
        menu = tk.Menu(self.root, tearoff=False)
        menu.configure(
            background=self.theme_colors["field"],
            foreground=self.theme_colors["foreground"],
            activebackground=self.theme_colors["active"],
            activeforeground=self.theme_colors["foreground"],
        )
        menu.add_command(label="Open File", command=lambda: self.open_path(file_path))
        menu.add_command(
            label="Open Folder Containing File",
            command=lambda: self.open_containing_folder(file_path),
        )
        menu.add_separator()
        menu.add_command(
            label="Unmark as duplicate"
            if values[2] == "duplicate"
            else "Mark as duplicate",
            command=lambda: self.toggle_duplicate_status(file_path),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
        return "break"

    def toggle_duplicate_status(self, path: Path) -> None:
        for group in self.duplicate_data.values():
            if group.original == path:
                replacement = group.duplicates.pop(0)
                group.duplicates.append(group.original)
                group.original = replacement
                self.checked_paths.discard(path)
                self.refresh_tree()
                return
            if path in group.duplicates:
                group.duplicates.remove(path)
                group.duplicates.append(group.original)
                group.original = path
                self.checked_paths.discard(path)
                self.refresh_tree()
                return

    def reset_preview(self) -> None:
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            160,
            160,
            text="No Preview Available",
            fill=self.theme_colors.get("muted", "#888888"),
        )
