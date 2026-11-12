from __future__ import annotations

import html
import unicodedata
from datetime import datetime
from pathlib import Path

import streamlit as st

from pet_component import load_codex_pet, pet

ROOT = Path(__file__).parent
PET_DIRS = {
    "clawd": ROOT / "assets" / "pets" / "clawd",
    "peach": ROOT / "assets" / "pets" / "peach-cat",
}
MOCHI = "Mochi (SVG integrado)"
CLAWD = "Clawd (atlas Codex v2)"
PEACH = "Peach (atlas Codex v2)"
PET_NAMES = {MOCHI: "Mochi", CLAWD: "Clawd", PEACH: "Peach"}
USERNAME = "Alex"
META_POSITIONS = {
    "Arriba izquierda": "above-left",
    "Arriba derecha": "above-right",
    "Abajo izquierda": "below-left",
    "Abajo derecha": "below-right",
}
MESSAGE_ACTIONS = ["Valorar", "Reiniciar desde aquí", "Bifurcar desde aquí"]

CHAT_CSS = """
<style>
  [data-testid="stChatMessage"]:has([data-testid="stMenuButton"]) {
    position: relative;
    overflow: visible !important;
  }

  [data-testid="stChatMessage"]:has(.chat-meta) [data-testid="stElementContainer"]:has(.chat-meta) {
    position: static !important;
  }

  .chat-meta {
    position: absolute;
    z-index: 2;
    color: var(--st-text-color, #6b5a4c);
    font-size: 0.66rem;
    font-weight: 500;
    line-height: 1.2;
    opacity: 0.58;
    white-space: nowrap;
    pointer-events: none;
    width: 6.75rem;
  }

  .chat-meta.pos-above-left {
    bottom: calc(100% + 6px);
    left: 0.15rem;
    text-align: left;
  }

  .chat-meta.pos-above-right {
    bottom: calc(100% + 6px);
    right: 1.4rem;
    text-align: right;
  }

  .chat-meta.pos-below-left {
    top: calc(100% + 6px);
    left: 0.15rem;
    text-align: left;
  }

  .chat-meta.pos-below-right {
    top: calc(100% + 6px);
    right: 1.4rem;
    text-align: right;
  }

  [data-testid="stChatMessage"] [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
    position: absolute;
    top: -1.35rem;
    right: 0;
    z-index: 5;
    width: auto;
    margin: 0;
  }

  [data-testid="stChatMessage"]:has(.chat-meta.pos-above-left) [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
    top: auto;
    bottom: calc(100% + 0.5px);
    left: 6.8rem;
    right: auto;
    transform: none;
  }

  [data-testid="stChatMessage"]:has(.chat-meta.pos-above-right) [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
    top: auto;
    bottom: calc(100% + 0.5px);
    left: auto;
    right: 0.15rem;
    transform: none;
  }

  [data-testid="stChatMessage"]:has(.chat-meta.pos-below-left) [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
    top: calc(100% - 1.5px);
    bottom: auto;
    left: 6.8rem;
    right: auto;
    transform: none;
  }

  [data-testid="stChatMessage"]:has(.chat-meta.pos-below-right) [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
    top: calc(100% - 1.5px);
    bottom: auto;
    left: auto;
    right: 0.15rem;
    transform: none;
  }

  [data-testid="stChatMessage"] [data-testid="stMenuButton"],
  [data-testid="stChatMessage"] [data-testid="stMenuButtonButton"] {
    width: auto !important;
  }

  [data-testid="stChatMessage"] [data-testid="stMenuButton"] button {
    min-height: 1.3rem;
    height: 1.3rem;
    padding: 0 0.4rem;
    border-radius: 999px;
    color: var(--st-text-color, #6b5a4c);
    font-size: 0.66rem;
    font-weight: 500;
    line-height: 1;
    opacity: 0.58;
  }

  [data-testid="stChatMessage"] [data-testid="stMenuButton"] svg,
  [data-testid="stChatMessage"] [data-testid="stMenuButton"] div[aria-hidden="true"] {
    display: none;
  }
</style>
"""

LANDING_CSS = """
<style>
  main.stMain {
    position: relative;
  }

  [data-testid="stBottom"] {
    position: absolute;
    top: 50%;
    bottom: auto;
    transform: translateY(-50%);
  }

  .pet-landing {
    position: fixed;
    left: 50%;
    bottom: calc(50% + 92px);
    transform: translateX(-50%);
    z-index: 100;
    width: min(704px, calc(100vw - 48px));
    text-align: center;
    pointer-events: none;
    animation: pet-landing-rise 420ms cubic-bezier(0.22, 1, 0.36, 1) both;
  }

  .pet-landing h1 {
    margin: 0 0 0.55rem;
    color: var(--st-text-color, #2b2118);
    font-size: clamp(2.35rem, 5vw, 3.8rem);
    font-weight: 800;
    letter-spacing: -0.045em;
    line-height: 1.02;
  }

  .pet-landing p {
    margin: 0;
    color: var(--st-text-color, #6b5a4c);
    font-size: clamp(1rem, 1.6vw, 1.15rem);
    opacity: 0.7;
  }

  @keyframes pet-landing-rise {
    from {
      opacity: 0;
      transform: translate(-50%, 14px);
    }
    to {
      opacity: 1;
      transform: translate(-50%, 0);
    }
  }

  @media (max-height: 560px) {
    .pet-landing {
      display: none;
    }
  }
</style>
"""

st.set_page_config(page_title="Streamlit Pets", layout="centered")

# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

if "pet_choice" not in st.session_state:
    st.session_state.pet_choice = MOCHI
if "pet_state" not in st.session_state:
    st.session_state.pet_state = "waving"
if "pet_message" not in st.session_state:
    st.session_state.pet_message = "¡Hola! Soy Mochi. Escríbeme algo o hazme click."
if "pokes" not in st.session_state:
    st.session_state.pokes = 0
if "messages" not in st.session_state:
    st.session_state.messages = []


def current_pet_name() -> str:
    return PET_NAMES.get(st.session_state.pet_choice, "Mochi")


def set_mood(state: str, message: str) -> None:
    st.session_state.pet_state = state
    st.session_state.pet_message = message


def on_pet_change() -> None:
    name = current_pet_name()
    set_mood("waving", f"¡Hola! Soy {name}. ¿Qué hacemos hoy?")


def on_poke() -> None:
    st.session_state.pokes += 1
    set_mood("jumping", "¡Jeje! Eso hace cosquillas.")


def reset_pet() -> None:
    st.session_state.pokes = 0
    st.session_state.messages = []
    set_mood("waving", f"¡Hola de nuevo! Soy {current_pet_name()}.")


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def mood_for(text: str) -> str:
    clean = normalize(text)
    rules = [
        (("hola", "hey", "hi", "buenas", "saluda"), "waving"),
        (("juega", "jugar", "pelota", "corre", "run"), "running-right"),
        (("salta", "brinca", "jump"), "jumping"),
        (("duerme", "dormir", "sueno", "sleep", "descansa"), "sleeping"),
        (("triste", "mal", "error", "fail", "llora"), "failed"),
        (("espera", "wait", "turno", "paciencia"), "waiting"),
        (("revisa", "mira", "review", "lee", "analiza"), "review"),
        (("trabaja", "working", "codigo", "programa", "procesa"), "running"),
        (("gracias", "buen", "bien", "genial"), "jumping"),
    ]
    for keywords, state in rules:
        if any(keyword in clean for keyword in keywords):
            return state
    return "idle"


def handle_message(text: str) -> None:
    reply = f"{text} ✨"
    st.session_state.pet_state = mood_for(text)
    st.session_state.pet_message = reply
    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
            "username": USERNAME,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
    )
    st.session_state.messages.append({"role": "assistant", "content": reply})


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

prompt = st.chat_input("Dile algo a tu mascota: hola, juega, duerme...")
if prompt:
    handle_message(prompt)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Mascota")
    st.radio(
        "Elige un renderer",
        [MOCHI, CLAWD, PEACH],
        key="pet_choice",
        on_change=on_pet_change,
    )
    size = st.slider("Tamaño", min_value=160, max_value=300, value=220, step=20)
    pixelated = st.toggle("Pixel art nítido", value=True)
    floating = st.toggle(
        "Flotar en la esquina",
        value=True,
        help="Ancla la mascota abajo a la derecha, junto al chat.",
    )
    st.radio(
        "Posición fecha/hora",
        list(META_POSITIONS),
        index=list(META_POSITIONS).index("Arriba derecha"),
        key="meta_corner_v2",
        help="Dónde mostrar el nombre, la fecha y la hora de cada mensaje.",
    )

    st.divider()
    st.subheader("Controles")
    st.caption(
        f"Pokes: **{st.session_state.pokes}** · Estado: "
        f"`{st.session_state.pet_state}`"
    )

    actions = [
        ("Saludar", "waving", "¡Hola! ¿Cómo estás?"),
        ("Jugar", "jumping", "¡Yuju! Otra vez."),
        ("Dormir", "sleeping", "Zzz... cinco minutitos."),
        ("Trabajar", "running", "Procesando..."),
        ("Revisar", "review", "Revisando con lupa."),
        ("Triste", "failed", "Aw... ¿un abrazo?"),
    ]
    action_columns = st.columns(2)
    for index, (label, state, message) in enumerate(actions):
        with action_columns[index % 2]:
            st.button(
                label,
                key=f"action_{state}",
                use_container_width=True,
                on_click=set_mood,
                args=(state, message),
            )

    st.divider()
    st.button("Reiniciar mascota", use_container_width=True, on_click=reset_pet)
    st.caption(
        "Clawd y Peach se cargan con el contrato de atlas de Codex: celdas de "
        "192x208, 8 columnas y filas de animación. Peach Cat es fan art de "
        "Peach and Goma (no hay Goma en el catálogo)."
    )

    with st.expander("Cómo funciona el componente"):
        st.code(
            """from pet_component import pet, load_codex_pet

pet(
    state="waving",                 # fila del atlas Codex
    message="¡Hola desde Streamlit!",
    sprite=load_codex_pet("assets/pets/peach-cat"),
    floating=True,                 # esquina inferior derecha
    key="pet",
    on_poke=lambda: None,          # trigger "poked"
)""",
            language="python",
        )
        st.markdown(
            "El frontend es JavaScript vanilla sobre Canvas/SVG. Para un atlas "
            "v2 usa las filas 0-8 como estados y las filas 9-10 para las 16 "
            "miradas."
        )

# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

pet_choice = st.session_state.pet_choice
if pet_choice == CLAWD:
    sprite = load_codex_pet(PET_DIRS["clawd"])
elif pet_choice == PEACH:
    sprite = load_codex_pet(PET_DIRS["peach"])
else:
    sprite = None

pet_size = min(size, 190) if floating else size
pet_kwargs = {
    "state": st.session_state.pet_state,
    "message": st.session_state.pet_message,
    "sprite": sprite,
    "size": pet_size,
    "pixelated": pixelated,
    "pet_name": current_pet_name(),
    "key": "pet",
    "on_poke": on_poke,
}

pet(floating=floating, **pet_kwargs)

# ---------------------------------------------------------------------------
# Main pane
# ---------------------------------------------------------------------------

if not st.session_state.messages:
    st.markdown(
        LANDING_CSS
        + (
            "<div class=\"pet-landing\">"
            "<h1>Hello, world!</h1>"
            f"<p>Dile algo a {current_pet_name()} para empezar.</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
else:
    st.markdown(CHAT_CSS, unsafe_allow_html=True)
    meta_position = META_POSITIONS[st.session_state.meta_corner_v2]
    for index, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                username = html.escape(str(message.get("username", USERNAME)))
                timestamp = html.escape(str(message.get("timestamp", "—")))
                text = html.escape(str(message["content"]))
                st.markdown(
                    f'<div class="chat-meta pos-{meta_position}">'
                    f"{username} · {timestamp}"
                    "</div>\n\n"
                    f"{text}",
                    unsafe_allow_html=True,
                )
                action = st.menu_button(
                    "≡",
                    MESSAGE_ACTIONS,
                    key=f"message_menu_{index}",
                    type="tertiary",
                )
                if action:
                    st.toast(f"{action}: próximamente")
            else:
                st.markdown(message["content"])
