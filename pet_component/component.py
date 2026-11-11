"""A bidirectional Streamlit pet component (Codex sprite atlas aware)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import streamlit as st

_FRONTEND = Path(__file__).parent / "frontend"
_HTML = (_FRONTEND / "pet.html").read_text(encoding="utf-8")
_CSS = (_FRONTEND / "pet.css").read_text(encoding="utf-8")
_JS = (_FRONTEND / "pet.js").read_text(encoding="utf-8")

_pet_component = st.components.v2.component(
    name="streamlit_pets_pet",
    html=_HTML,
    css=_CSS,
    js=_JS,
)


def _noop() -> None:
    return None


def pet(
    *,
    state: str = "idle",
    message: str | None = None,
    look: tuple[float, float] | None = None,
    sprite: dict[str, Any] | None = None,
    size: int = 220,
    pixelated: bool = True,
    floating: bool = False,
    pet_name: str = "Mochi",
    key: str | None = None,
    on_poke: Callable[[], None] | None = None,
) -> Any:
    """Mount the pet and return Streamlit's component result.

    Parameters
    ----------
    state:
        One of ``idle``, ``running-right``, ``running-left``, ``waving``,
        ``jumping``, ``failed``, ``waiting``, ``running``, ``review`` or
        ``sleeping``. These map directly to the nine standard Codex rows.
    message:
        Text shown in the pet's speech bubble. ``None`` hides the bubble.
    look:
        Normalized ``(x, y)`` gaze direction. On a v2 atlas, idle uses the
        16 look-direction cells when the vector is long enough.
    sprite:
        Payload returned by :func:`pet_component.load_codex_pet`. When omitted,
        the built-in SVG pet is rendered.
    size:
        Rendered height of the pet in pixels.
    pixelated:
        Keep hard pixel edges when scaling the atlas.
    floating:
        Pin the pet to the bottom-right corner of the viewport. The component
        mount takes almost no layout space, so it behaves like a desktop pet
        next to Streamlit's chat input.
    pet_name:
        Name sent back with the ``poked`` trigger and used for accessibility.
    key:
        Streamlit key for this component instance.
    on_poke:
        Optional callback executed when the user clicks / activates the pet.
        The component result exposes the latest event as ``result.poked``.
    """

    height = 1 if floating else max(220, int(size) + 100)
    data = {
        "state": state,
        "message": message or "",
        "look": list(look) if look is not None else [0.0, 0.0],
        "sprite": sprite,
        "size": int(size),
        "pixelated": bool(pixelated),
        "floating": bool(floating),
        "petName": pet_name,
    }

    return _pet_component(
        data=data,
        key=key,
        width="content" if floating else "stretch",
        height=height,
        on_poked_change=on_poke or _noop,
    )
