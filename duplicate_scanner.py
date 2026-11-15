import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image
from send2trash import send2trash


ImageDimensions = Optional[Tuple[int, int]]


@dataclass
class DuplicateGroup:
    extension: str
    size: int
    dimensions: ImageDimensions
    original: Path
    duplicates: List[Path]


class DuplicateScanner:
    """Find files with matching extension, size, dimensions, and content."""

    @staticmethod
    def get_file_hash(filepath: Path, chunk_size: int = 65536) -> Optional[str]:
        hasher = hashlib.md5()
        try:
            with filepath.open("rb") as file:
                while chunk := file.read(chunk_size):
                    hasher.update(chunk)
        except OSError:
            return None
        return hasher.hexdigest()

    @staticmethod
    def get_image_dimensions(filepath: Path) -> ImageDimensions:
        try:
            with Image.open(filepath) as image:
                return image.size
        except (OSError, ValueError):
            return None

    def scan_directory(self, target_directory: str) -> Dict[str, DuplicateGroup]:
        target_path = Path(target_directory)
        if not target_path.is_dir():
            return {}

        candidates: Dict[Tuple[str, int, ImageDimensions], List[Path]] = {}
        for file_path in target_path.rglob("*"):
            if not file_path.is_file():
                continue
            try:
                key = (
                    file_path.suffix.lower(),
                    file_path.stat().st_size,
                    self.get_image_dimensions(file_path),
                )
            except OSError:
                continue
            candidates.setdefault(key, []).append(file_path)

        duplicates: Dict[str, DuplicateGroup] = {}
        group_id = 1
        for (extension, size, dimensions), paths in candidates.items():
            if len(paths) < 2:
                continue

            hash_groups: Dict[str, List[Path]] = {}
            for path in paths:
                file_hash = self.get_file_hash(path)
                if file_hash:
                    hash_groups.setdefault(file_hash, []).append(path)

            for identical_paths in hash_groups.values():
                if len(identical_paths) < 2:
                    continue
                duplicates[f"Group {group_id}"] = DuplicateGroup(
                    extension=extension or "None",
                    size=size,
                    dimensions=dimensions,
                    original=identical_paths[0],
                    duplicates=identical_paths[1:],
                )
                group_id += 1

        return duplicates


class DuplicateFileManager:
    """Perform file actions independently of the user interface."""

    @staticmethod
    def move_to_recycle_bin(filepath: str) -> None:
        send2trash(filepath)
