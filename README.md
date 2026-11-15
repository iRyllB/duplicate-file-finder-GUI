# Duplicate File Finder GUI

## Introduction

Duplicate File Finder GUI is a desktop application that helps you find identical
files in a folder and its subfolders. It compares file type, size, image
dimensions, and file content before grouping duplicates. You can review the
results and send selected duplicate files to the Windows Recycle Bin.

The project uses Python and Tkinter for the interface, Pillow for image
information and previews, and send2trash for safe file removal.

## Requirements

Before starting, install:

- Python 3.9 or newer
- Git
- Windows (the application sends deleted files to the Windows Recycle Bin)

## Installation

### 1. Clone the repository

Open PowerShell or Command Prompt and run:

```powershell
git clone https://github.com/iRyllB/duplicate-file-finder-GUI.git
cd duplicate-file-finder-GUI
```

### 2. Create a virtual environment (Optional)

Creating a virtual environment keeps this project's packages separate from
your other Python projects:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If you are using Command Prompt instead, run:

```bat
.venv\Scripts\activate
```

### 3. Install the requirements

Install the packages listed in `requirements.txt`:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Running the application

Make sure the virtual environment is activated, then run the main launcher:

```powershell
python gui_duplicator.py
```

Do not run `duplicate_app.py` or `duplicate_scanner.py` directly. They are
modules used by `gui_duplicator.py`.

## How to use the application

1. Click **Browse** and choose the folder you want to scan.
2. Click **Scan for Duplicates**.
3. Use **Recheck Folder** after files are added, deleted, or changed.
4. Review the duplicate groups in the left panel.
5. Select one or more files to view their details and image preview.
6. Click the checkbox in the **Delete** column for each duplicate you want to remove.
7. Click **Delete All Selected** and confirm the deletion.

The first file in each duplicate group is marked **[KEEP ORIGINAL]**. Review
each group before removing a file.

Use **Delete All Duplicates** to send every file marked **[DUPLICATE]** to the
Windows Recycle Bin after one confirmation. Original files are never included
in this action.

The **Delete all duplicates** checkbox selects or clears every duplicate in the
delete column without deleting immediately. Use **Delete All Selected** to
confirm and move the checked files to the Recycle Bin.

Use **Show all original** to hide duplicate rows, or **Show all duplicates** to
hide original rows. These filters only change what is displayed.

Double-click a file to open it. Right-click a file for these options:

- **Open File**
- **Open Folder Containing File**
- **Mark as duplicate** or **Unmark as duplicate**

Files marked as duplicates are shown in a different color. Marking a file as a
duplicate makes it eligible for the delete checkboxes; unmarking it makes it
the original for that group.

The application detects your Windows app theme when it starts. Use
**Switch to Dark Mode** or **Switch to Light Mode** to change the theme while
the application is running.

## Project structure

```text
duplicate-file-finder-GUI/
├── duplicate_app.py       # Tkinter user interface
├── duplicate_scanner.py   # Scanning and file-management logic
├── gui_duplicator.py      # Application entry point
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Troubleshooting

- If `python` is not recognized, install Python and enable **Add Python to
  PATH** during installation.
- If PowerShell blocks activation, run PowerShell as your user and execute:
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.
- If a package is missing, activate `.venv` and run the requirements install
  command again.