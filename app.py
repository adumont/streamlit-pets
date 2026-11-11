from __future__ import annotations

import unicodedata
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
    st.session_state.messages.append({"role": "user", "content": text})
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
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
