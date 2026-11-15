import tkinter as tk

from duplicate_app import DuplicateApp

__all__ = ["DuplicateApp"]


def main() -> None:
    root = tk.Tk()
    DuplicateApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
