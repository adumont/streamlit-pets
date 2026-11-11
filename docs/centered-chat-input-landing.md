# Centered `st.chat_input` with a ChatGPT-style greeting

This guide documents how the landing screen in `app.py` puts Streamlit's
`st.chat_input` in the middle of the main pane, with a greeting above it. After
the first user message, the input returns to Streamlit's normal bottom position
and the main pane becomes a conversation transcript.

Tested with Streamlit `1.67.0` on Windows/Chrome. The CSS relies on Streamlit's
DOM (`stBottom`, `stMain`), so re-check the selectors if you upgrade Streamlit.

## Target behavior

1. Before any message:
   - Large centered greeting.
   - `st.chat_input` centered horizontally and vertically in the main pane.
   - Sidebar remains visible.
2. After the first message:
   - The greeting and landing CSS disappear.
   - `st.chat_input` returns to the normal sticky bottom position.
   - The main pane shows only the conversation messages.
3. Resetting the conversation restores the landing state.

## Why this needs CSS

`st.chat_input` always renders inside Streamlit's bottom container
(`[data-testid="stBottom"]`). There is no built-in "inline" or "centered"
argument. The implementation temporarily overrides that container's layout with
CSS, then removes the override after the first message.

Do not replace `st.chat_input` with a custom form. That changes its appearance,
keyboard behavior, and submit semantics. Move the real widget instead.

## Implementation

### 1. Track conversation state

The landing state is derived from the message list:

```python
if "messages" not in st.session_state:
    st.session_state.messages = []
```

`messages` contains dictionaries such as:

```python
{"role": "user", "content": "hola"}
{"role": "assistant", "content": "hola ✨"}
```

### 2. Call `st.chat_input` before rendering the conditional layout

This ordering is important. The widget's return value must be processed before
deciding whether to emit the landing CSS. On submit, Streamlit reruns the
script; the prompt is available immediately, so update the state in the same
run.

```python
prompt = st.chat_input("Dile algo a tu mascota: hola, juega, duerme...")
if prompt:
    handle_message(prompt)
```

`handle_message` appends the user message and the loopback reply:

```python
def handle_message(text: str) -> None:
    reply = f"{text} ✨"
    st.session_state.pet_state = mood_for(text)
    st.session_state.pet_message = reply
    st.session_state.messages.append({"role": "user", "content": text})
    st.session_state.messages.append({"role": "assistant", "content": reply})
```

Do **not** call `st.rerun()` after `handle_message` for this pattern. The state
is already updated before the rest of the script renders, so an extra rerun only
adds flicker.

### 3. Emit the landing CSS and greeting only when there are no messages

```python
if not st.session_state.messages:
    st.markdown(
        LANDING_CSS
        + (
            "<div class=\"pet-landing\">"
            "<h1>Hello, world!</h1>"
            "<p>Dile algo a tu mascota para empezar.</p>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
```

When the first message exists, `LANDING_CSS` is no longer emitted. The browser
drops the style element, and `stBottom` falls back to its native sticky bottom
layout.

### 4. Use this CSS

```python
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
```

## Why each part works

### `main.stMain { position: relative }`

`stBottom` is a child of `<main class="stMain">` in Streamlit 1.67. Making the
main element the positioning context means the chat container is centered inside
the **content pane**, not the whole viewport. This matters when a sidebar is
open; a viewport-centered layout would be shifted left relative to the content.

### `[data-testid="stBottom"] { position: absolute; top: 50%; ... }`

`stBottom` normally uses `position: sticky; bottom: 0`. Overriding it with
`position: absolute; top: 50%` inside the relative main pane centers the whole
bottom container vertically. `bottom: auto` is required to undo the sticky
bottom offset.

The chat input itself keeps its original width, background, border, radius, and
placeholder styling. Only its container is repositioned.

### `.pet-landing { position: fixed; bottom: calc(50% + 92px) }`

The greeting is fixed above the centered chat container:

- `bottom: calc(50% + 92px)` places its bottom edge about 92 px above the
  viewport's vertical midpoint.
- `width: min(704px, calc(100vw - 48px))` matches Streamlit's centered content
  width while remaining responsive.
- `pointer-events: none` ensures the greeting never blocks the chat input.
- `z-index: 100` keeps it above the main content.

The `92px` offset is tuned for the current bottom-container padding. If you
change Streamlit versions or theme spacing, adjust this value after inspecting
the rendered result.

## Verification checklist

Use a browser with DevTools or an automation tool:

1. Load the app with an empty `messages` list.
2. Confirm the greeting is centered above the chat input.
3. Confirm the chat input is horizontally centered in the main pane, not in the
   full viewport.
4. Type a message and submit it.
5. Confirm:
   - The greeting disappears.
   - The chat input moves to the bottom.
   - The conversation shows the user message and the assistant loopback reply.
6. Click "Reiniciar mascota" or clear `messages`.
7. Confirm the centered landing state returns.

Useful DOM checks:

```js
document.querySelector('[data-testid="stBottom"]').getBoundingClientRect()
document.querySelector('[data-testid="stChatInput"]').getBoundingClientRect()
document.querySelector('main.stMain').getBoundingClientRect()
```

Before the first message, `stBottom` should be vertically near the middle of
`main.stMain`. After the first message, it should be near the bottom.

## Common mistakes

- **Calling `st.chat_input` after the conditional CSS.** On submit, the landing
  CSS may still be emitted for that rerun. Call the widget and process its prompt
  first.
- **Using `st.rerun()` after handling the prompt.** This causes an unnecessary
  second rerun and can flash the layout.
- **Using `position: fixed` on `stBottom`.** It centers against the viewport,
  which is wrong when the sidebar is open. Use `absolute` inside `main.stMain`.
- **Removing the streamlit container background.** Do not restyle the inner chat
  input unless the design requires it. Position the container only.
- **Assuming the selectors are stable forever.** `stBottom`, `stMain`, and
  `stChatInput` are Streamlit test IDs. Re-inspect the DOM after upgrading.

## Relevant project files

- `app.py`: `LANDING_CSS`, `handle_message`, conditional landing/conversation.
- `app.py:159`: `st.chat_input` call.
- `app.py:267`: landing vs. conversation rendering.
