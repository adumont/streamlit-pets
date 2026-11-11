"""Load Codex-compatible pet packages (pet.json + spritesheet.webp)."""

from __future__ import annotations

import base64
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

FRAME_WIDTH = 192
FRAME_HEIGHT = 208


@lru_cache(maxsize=16)
def _read_pet_dir(pet_dir: str) -> tuple[str, str, int]:
    directory = Path(pet_dir).resolve()
    manifest_path = directory / "pet.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"No existe pet.json en {directory}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    relative_sheet = str(manifest.get("spritesheetPath") or "spritesheet.webp")
    sheet_path = (directory / relative_sheet).resolve()

    # Keep reads inside the pet package.
    try:
        sheet_path.relative_to(directory)
    except ValueError as exc:
        raise ValueError(
            f"spritesheetPath must stay inside {directory}: {relative_sheet!r}"
        ) from exc

    if not sheet_path.is_file():
        raise FileNotFoundError(f"No existe el spritesheet: {sheet_path}")

    mime = "image/webp" if sheet_path.suffix.lower() == ".webp" else "image/png"
    encoded = base64.b64encode(sheet_path.read_bytes()).decode("ascii")
    data_url = f"data:{mime};base64,{encoded}"

    version = int(manifest.get("spriteVersionNumber") or 1)
    name = str(manifest.get("displayName") or manifest.get("id") or directory.name)
    return name, data_url, version


def load_codex_pet(pet_dir: str | Path) -> dict[str, Any]:
    """Return a JSON-serializable sprite payload for :func:`pet`.

    The folder must follow the Codex pet contract: a ``pet.json`` manifest and
    a ``spritesheet.webp`` atlas with 192x208 cells (8 columns).
    """

    name, data_url, version = _read_pet_dir(str(Path(pet_dir)))
    return {
        "name": name,
        "dataUrl": data_url,
        "version": version,
        "frameWidth": FRAME_WIDTH,
        "frameHeight": FRAME_HEIGHT,
    }
