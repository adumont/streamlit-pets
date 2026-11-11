from __future__ import annotations

import unicodedata
from pathlib import Path

import streamlit as st

from pet_component import load_codex_pet, pet

ROOT = Path(__file__).parent
CLAWD_DIR = ROOT / "assets" / "pets" / "clawd"
MOCHI = "Mochi (SVG integrado)"
CLAWD = "Clawd (atlas Codex v2)"

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
if "last_exchange" not in st.session_state:
    st.session_state.last_exchange = None


def current_pet_name() -> str:
    return "Clawd" if st.session_state.pet_choice == CLAWD else "Mochi"


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
    st.session_state.last_exchange = None
    set_mood("waving", f"¡Hola de nuevo! Soy {current_pet_name()}.")


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def reply_for(text: str) -> tuple[str, str]:
    clean = normalize(text)
    rules = [
        (("hola", "hey", "hi", "buenas", "saluda"), "waving", "¡Hola! Me alegra verte."),
        (("juega", "jugar", "pelota", "corre", "run"), "running-right", "¡A correr! Sígueme."),
        (("salta", "brinca", "jump"), "jumping", "¡Boing! ¡Boing!"),
        (("duerme", "dormir", "sueno", "sleep", "descansa"), "sleeping", "Zzz... cinco minutitos."),
        (("triste", "mal", "error", "fail", "llora"), "failed", "Aw... ¿me das un abrazo?"),
        (("espera", "wait", "turno", "paciencia"), "waiting", "Esperando tu siguiente mensaje..."),
        (("revisa", "mira", "review", "lee", "analiza"), "review", "Revisando todo con lupa."),
        (("trabaja", "working", "codigo", "programa", "procesa"), "running", "Trabajando duro..."),
        (("gracias", "buen", "bien", "genial"), "jumping", "¡Gracias a ti!"),
    ]
    for keywords, state, reply in rules:
        if any(keyword in clean for keyword in keywords):
            return state, reply
    return "idle", "Te escucho. Prueba con: hola, juega, salta, duerme, trabaja o revisa."


def handle_message(text: str) -> None:
    state, reply = reply_for(text)
    st.session_state.pet_state = state
    st.session_state.pet_message = reply
    st.session_state.last_exchange = (text, reply)


# ---------------------------------------------------------------------------
# Hello world + message input
# ---------------------------------------------------------------------------

st.title("Hello, world!")
st.write(
    "Este es el *hello world* de Streamlit, con un extra: un componente de "
    "mascota bidireccional compatible con los sprites de "
    "[awesome-codex-pet](https://github.com/legeling/awesome-codex-pet)."
)

prompt = st.chat_input("Dile algo a tu mascota: hola, juega, duerme...")
if prompt:
    handle_message(prompt)

st.divider()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Mascota")
    st.radio(
        "Elige un renderer",
        [MOCHI, CLAWD],
        key="pet_choice",
        on_change=on_pet_change,
    )
    size = st.slider("Tamaño", min_value=160, max_value=300, value=220, step=20)
    pixelated = st.toggle("Pixel art nítido", value=True)
    st.divider()
    st.caption(
        "Clawd se carga desde `assets/pets/clawd/` con el contrato de atlas "
        "de Codex: celdas de 192x208, 8 columnas y filas de animación."
    )
    st.button("Reiniciar mascota", use_container_width=True, on_click=reset_pet)

# ---------------------------------------------------------------------------
# Pet + controls
# ---------------------------------------------------------------------------

pet_col, controls_col = st.columns([1.35, 1], gap="large")

with pet_col:
    sprite = load_codex_pet(CLAWD_DIR) if st.session_state.pet_choice == CLAWD else None
    pet(
        state=st.session_state.pet_state,
        message=st.session_state.pet_message,
        sprite=sprite,
        size=size,
        pixelated=pixelated,
        pet_name=current_pet_name(),
        key="pet",
        on_poke=on_poke,
    )
    st.caption(
        f"Pokes: **{st.session_state.pokes}** · Estado: "
        f"`{st.session_state.pet_state}`"
    )

with controls_col:
    st.subheader("Hablar con la mascota")
    st.caption(
        "Los mensajes van de Python al componente con `data`. Los clicks de la "
        "mascota vuelven a Python como trigger `poked`."
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

    if st.session_state.last_exchange:
        user_text, reply = st.session_state.last_exchange
        st.divider()
        st.markdown(f"**Tú:** {user_text}")
        st.markdown(f"**{current_pet_name()}:** {reply}")

with st.expander("Cómo funciona el componente"):
    st.code(
        """from pet_component import pet, load_codex_pet

pet(
    state="waving",                 # fila del atlas Codex
    message="¡Hola desde Streamlit!",
    sprite=load_codex_pet("assets/pets/clawd"),
    key="pet",
    on_poke=lambda: None,          # trigger "poked"
)""",
        language="python",
    )
    st.markdown(
        "El frontend es JavaScript vanilla sobre Canvas/SVG. Para un atlas v2 "
        "usa las filas 0-8 como estados y las filas 9-10 para las 16 miradas."
    )
