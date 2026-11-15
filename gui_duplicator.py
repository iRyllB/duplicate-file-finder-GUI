import os
import hashlib
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from send2trash import send2trash

# ==========================================
# BACKEND MODULE: Scanning & Logic
# ==========================================
class DuplicateScanner:
    @staticmethod
    def get_file_hash(filepath, chunk_size=65536):
        """Calculates the MD5 hash of a file to verify exact content match."""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception:
            return None

    @staticmethod
    def get_image_dimensions(filepath):
        """Returns width and height if the file is a valid image, otherwise None."""
        try:
            with Image.open(filepath) as img:
                return img.size  # (width, height)
        except Exception:
            return None

    def scan_directory(self, target_directory):
        """Scans directory and returns structured groups of identical files."""
        target_path = Path(target_directory)
        if not target_path.exists():
            return {}

        file_groups = {}
        for file_path in target_path.rglob('*'):
            if file_path.is_file():
                try:
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower()
                    dimensions = self.get_image_dimensions(file_path)

                    key = (file_ext, file_size, dimensions)
                    if key not in file_groups:
                        file_groups[key] = []
                    file_groups[key].append(file_path)
                except Exception:
                    continue

        # Filter for actual duplicates and verify via MD5 hash
        verified_duplicates = {}
        group_id = 1

        for key, paths in file_groups.items():
            if len(paths) > 1:
                ext, size, dims = key
                hash_groups = {}
                for p in paths:
                    file_hash = self.get_file_hash(p)
                    if file_hash:
                        if file_hash not in hash_groups:
                            hash_groups[file_hash] = []
                        hash_groups[file_hash].append(p)

                for file_hash, identical_paths in hash_groups.items():
                    if len(identical_paths) > 1:
                        verified_duplicates[f"Group {group_id}"] = {
                            "ext": ext or "None",
                            "size": size,
                            "dimensions": dims if dims else "N/A",
                            "original": identical_paths[0],
                            "duplicates": identical_paths[1:]
                        }
                        group_id += 1

        return verified_duplicates


# ==========================================
# FRONTEND MODULE: Graphical User Interface
# ==========================================
class DuplicateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Modular Duplicate File Cleaner")
        self.root.geometry("1050x650")
        
        self.scanner = DuplicateScanner()
        self.duplicate_data = {}
        self.current_preview_image = None

        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

    def create_widgets(self):
        # Top Frame: Directory selection and scan button
        top_frame = ttk.Frame(self.root, padding=10)
        top_frame.pack(fill=tk.X, side=tk.TOP)

        ttk.Label(top_frame, text="Target Folder:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        self.path_entry = ttk.Entry(top_frame, width=65)
        self.path_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        browse_btn = ttk.Button(top_frame, text="Browse", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT, padx=5)

        scan_btn = ttk.Button(top_frame, text="Scan for Duplicates", command=self.run_scan)
        scan_btn.pack(side=tk.LEFT, padx=5)

        # Main Split Pane (Left: Treeview list, Right: Preview/Details pane)
        main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Left Frame: Treeview of duplicates
        left_frame = ttk.Frame(main_pane)
        main_pane.add(left_frame, weight=3)

        self.tree = ttk.Treeview(left_frame, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        self.tree.heading("#0", text="Duplicates Tree (Format, Size, Dimensions matched)", anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", self.on_select_item)

        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        # Right Frame: Preview & Details
        right_frame = ttk.LabelFrame(main_pane, text=" File Preview & Details ", padding=10)
        main_pane.add(right_frame, weight=2)

        self.details_label = ttk.Label(right_frame, text="Select a file to view details.", font=("Segoe UI", 9), wraplength=350)
        self.details_label.pack(anchor=tk.W, pady=5)

        # Image Preview Canvas / Label
        self.preview_canvas = tk.Canvas(right_frame, bg="#f0f0f0", width=320, height=320)
        self.preview_canvas.pack(pady=10)
        self.preview_canvas.create_text(160, 160, text="No Preview Available", fill="#888888")

        # Bottom Action Bar
        bottom_frame = ttk.Frame(self.root, padding=10)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.delete_btn = ttk.Button(bottom_frame, text="Send Selected Duplicate to Recycle Bin", command=self.delete_selected, state=tk.DISABLED)
        self.delete_btn.pack(side=tk.RIGHT, padx=5)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder)

    def run_scan(self):
        target_dir = self.path_entry.get().strip()
        if not target_dir or not os.path.exists(target_dir):
            messagebox.showerror("Error", "Please select a valid directory first.")
            return

        # Clear previous tree data
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.duplicate_data = self.scanner.scan_directory(target_dir)

        if not self.duplicate_data:
            messagebox.showinfo("Result", "No duplicate files found matching your criteria!")
            return

        # Populate Treeview
        for group_name, info in self.duplicate_data.items():
            group_text = f"{group_name} | Ext: {info['ext']} | Size: {info['size']:,} bytes | Dims: {info['dimensions']}"
            parent_node = self.tree.insert("", tk.END, text=group_text, open=True)

            # Original (Keep)
            orig_text = f"[KEEP ORIGINAL] {info['original'].name}"
            self.tree.insert(parent_node, tk.END, text=orig_text, values=(str(info['original']), "original"))

            # Duplicates (To review)
            for dup in info['duplicates']:
                dup_text = f"[DUPLICATE] {dup.name}"
                self.tree.insert(parent_node, tk.END, text=dup_text, values=(str(dup), "duplicate"))

        messagebox.load = messagebox.showinfo("Scan Complete", f"Found {len(self.duplicate_data)} duplicate groups!")

    def on_select_item(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")

        if values:
            file_path, file_type = values
            self.load_file_details(file_path, file_type)
        else:
            self.delete_btn.config(state=tk.DISABLED)

    def load_file_details(self, file_path, file_type):
        path_obj = Path(file_path)
        if not path_obj.exists():
            return

        size = path_obj.stat().st_size
        ext = path_obj.suffix.lower()
        dims = self.scanner.get_image_dimensions(path_obj)

        info_text = f"File Name: {path_obj.name}\nPath: {file_path}\nType: {'Original (Safe)' if file_type=='original' else 'Duplicate'}\nSize: {size:,} bytes\nDimensions: {dims if dims else 'N/A'}"
        self.details_label.config(text=info_text)

        # Enable delete button only if it's explicitly a duplicate
        if file_type == "duplicate":
            self.delete_btn.config(state=tk.NORMAL)
        else:
            self.delete_btn.config(state=tk.DISABLED)

        # Load image preview if format matches image types
        self.preview_canvas.delete("all")
        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp', '.gif']:
            try:
                img = Image.open(file_path)
                img.thumbnail((300, 300))
                self.current_preview_image = ImageTk.PhotoImage(img)
                self.preview_canvas.create_image(160, 160, image=self.current_preview_image, anchor=tk.CENTER)
            except Exception:
                self.preview_canvas.create_text(160, 160, text="Could not load preview", fill="red")
        else:
            self.preview_canvas.create_text(160, 160, text="Preview available for images only", fill="#888888")

    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            return

        item = selected_items[0]
        values = self.tree.item(item, "values")
        if not values or values[1] != "duplicate":
            return

        file_path = values[0]
        file_name = Path(file_path).name

        confirm = messagebox.askyesno("Confirm Deletion", f"Are you sure you want to send this duplicate to the Recycle Bin?\n\n{file_name}")
        if confirm:
            try:
                send2trash(file_path)
                messagebox.showinfo("Success", "File safely moved to the Windows Recycle Bin.")
                # Remove from treeview
                self.tree.delete(item)
                self.delete_btn.config(state=tk.DISABLED)
                self.details_label.config(text="Select a file to view details.")
                self.preview_canvas.delete("all")
                self.preview_canvas.create_text(160, 160, text="No Preview Available", fill="#888888")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = DuplicateApp(root)
    root.mainloop()