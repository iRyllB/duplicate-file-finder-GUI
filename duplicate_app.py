from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

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
        self.current_preview_image = None
        self.is_dark_mode = self.detect_system_dark_mode()

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
                "selected": "#3c5a78",
                "canvas": "#303134",
                "muted": "#b8c0c8",
            }
        else:
            colors = {
                "background": "#f0f0f0",
                "foreground": "#202124",
                "field": "#ffffff",
                "selected": "#cfe2f3",
                "canvas": "#f0f0f0",
                "muted": "#666666",
            }

        self.root.configure(bg=colors["background"])
        self.preview_canvas.configure(bg=colors["canvas"])
        self.style.configure(".", background=colors["background"], foreground=colors["foreground"])
        self.style.configure(
            "TEntry",
            fieldbackground=colors["field"],
            foreground=colors["foreground"],
            insertcolor=colors["foreground"],
        )
        self.style.configure(
            "Treeview",
            background=colors["field"],
            fieldbackground=colors["field"],
            foreground=colors["foreground"],
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
            background=[("active", colors["selected"])],
            foreground=[("active", colors["foreground"])],
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
        ttk.Button(top_frame, text="Browse", command=self.browse_folder).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(top_frame, text="Scan for Duplicates", command=self.run_scan).pack(
            side=tk.LEFT, padx=5
        )
        self.theme_btn = ttk.Button(
            top_frame, text="Switch Theme", command=self.toggle_theme
        )
        self.theme_btn.pack(side=tk.LEFT, padx=5)

        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)
        self.tree = ttk.Treeview(left_frame, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.heading(
            "#0", text="Duplicates Tree (Format, Size, Dimensions matched)", anchor=tk.W
        )
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)
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
        self.delete_btn = ttk.Button(
            bottom_frame,
            text="Send Selected Duplicate to Recycle Bin",
            command=self.delete_selected,
            state=tk.DISABLED,
        )
        self.delete_btn.pack(side=tk.RIGHT, padx=5)
        self.delete_all_btn = ttk.Button(
            bottom_frame,
            text="Delete All Duplicates",
            command=self.delete_all_duplicates,
            state=tk.DISABLED,
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
        target_dir = self.path_entry.get().strip()
        if not target_dir or not Path(target_dir).is_dir():
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        self.clear_tree()
        self.duplicate_data = self.scanner.scan_directory(target_dir)
        if not self.duplicate_data:
            self.delete_all_btn.config(state=tk.DISABLED)
            messagebox.showinfo("Result", "No duplicate files found matching your criteria!")
            return

        self.populate_tree()
        self.delete_all_btn.config(state=tk.NORMAL)
        messagebox.showinfo(
            "Scan Complete", f"Found {len(self.duplicate_data)} duplicate groups!"
        )

    def populate_tree(self) -> None:
        for group_name, group in self.duplicate_data.items():
            group_text = (
                f"{group_name} | Ext: {group.extension} | "
                f"Size: {group.size:,} bytes | Dims: {group.dimensions or 'N/A'}"
            )
            parent_node = self.tree.insert("", tk.END, text=group_text, open=True)
            self.tree.insert(
                parent_node,
                tk.END,
                text=f"[KEEP ORIGINAL] {group.original.name}",
                values=(str(group.original), "original"),
            )
            for duplicate in group.duplicates:
                self.tree.insert(
                    parent_node,
                    tk.END,
                    text=f"[DUPLICATE] {duplicate.name}",
                    values=(str(duplicate), "duplicate"),
                )

    def clear_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

    def on_select_item(self, _event) -> None:
        selected_items = self.tree.selection()
        if not selected_items:
            return

        values = self.tree.item(selected_items[0], "values")
        if values:
            self.load_file_details(values[0], values[1])
        else:
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
        self.delete_btn.config(
            state=tk.NORMAL if file_type == "duplicate" else tk.DISABLED
        )

        self.preview_canvas.delete("all")
        if path_obj.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}:
            self.preview_canvas.create_text(
                160, 160, text="Preview available for images only", fill="#888888"
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

    def delete_selected(self) -> None:
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")
        if not values or values[1] != "duplicate":
            return

        file_path = values[0]
        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to send this duplicate to the Recycle Bin?\n\n"
            f"{Path(file_path).name}",
        ):
            return
        try:
            self.file_manager.move_to_recycle_bin(file_path)
        except OSError as error:
            messagebox.showerror("Error", f"Failed to delete file: {error}")
            return

        messagebox.showinfo("Success", "File safely moved to the Windows Recycle Bin.")
        self.remove_duplicate_from_data(Path(file_path))
        self.refresh_tree()
        self.delete_btn.config(state=tk.DISABLED)
        self.details_label.config(text="Select a file to view details.")
        self.reset_preview()

    def delete_all_duplicates(self) -> None:
        duplicate_paths = [
            duplicate
            for group in self.duplicate_data.values()
            for duplicate in group.duplicates
        ]
        if not duplicate_paths:
            self.delete_all_btn.config(state=tk.DISABLED)
            return

        if not messagebox.askyesno(
            "Confirm Deletion",
            f"Send all {len(duplicate_paths)} duplicate files to the Recycle Bin?",
        ):
            return

        deleted_paths = []
        failed_paths = []
        for path in duplicate_paths:
            try:
                self.file_manager.move_to_recycle_bin(str(path))
                deleted_paths.append(path)
            except OSError:
                failed_paths.append(path)

        for path in deleted_paths:
            self.remove_duplicate_from_data(path)
        self.refresh_tree()
        self.delete_btn.config(state=tk.DISABLED)
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

    def remove_duplicate_from_data(self, file_path: Path) -> None:
        for group_name, group in list(self.duplicate_data.items()):
            group.duplicates = [
                duplicate for duplicate in group.duplicates if duplicate != file_path
            ]
            if not group.duplicates:
                del self.duplicate_data[group_name]

    def refresh_tree(self) -> None:
        self.clear_tree()
        self.populate_tree()
        self.delete_all_btn.config(
            state=tk.NORMAL if self.duplicate_data else tk.DISABLED
        )

    def reset_preview(self) -> None:
        self.preview_canvas.delete("all")
        self.preview_canvas.create_text(
            160, 160, text="No Preview Available", fill="#888888"
        )
