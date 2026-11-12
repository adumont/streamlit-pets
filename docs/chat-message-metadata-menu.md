# Per-message metadata and menu in Streamlit chat

This guide documents how `app.py` adds a small metadata line to every **user**
chat message and places a one-character menu button on that same line.

The metadata line contains the username, date, and time:

```text
Alex · 12/11/2026 01:23 ≡
```

It sits **outside** the grey message bubble, at one of four corners:

- arriba izquierda
- arriba derecha
- abajo izquierda
- abajo derecha

The menu button uses `≡` (`U+2261`, identical to) and opens a Streamlit menu
with provisional actions. It is styled to match the metadata's color, opacity,
font size, and font weight.

Tested with Streamlit `1.67.0` on Windows/Chrome. The implementation relies on
Streamlit's DOM (`stChatMessage`, `stChatMessageContent`, `stElementContainer`,
`stMenuButton`) and CSS `:has()`. Re-inspect the DOM after upgrading Streamlit.

## Target behavior

1. Each user message stores `username` and `timestamp` when it is sent.
2. The metadata is rendered outside the message bubble, with a small gap.
3. The chat message bubble is **not** resized or moved.
4. The menu button appears on the metadata line, immediately to the right of
   the timestamp.
5. The metadata menu is only rendered for user messages. Assistant messages have
   no menu, which avoids an extra floating button near the previous message.
6. A sidebar radio chooses one of the four corners. The default is **Arriba
   derecha**.
7. Changing the radio repositions existing metadata without changing message
   content.

## Data model

Add the metadata when the user message is appended:

```python
from datetime import datetime

USERNAME = "Alex"


def handle_message(text: str) -> None:
    reply = f"{text} ✨"
    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
            "username": USERNAME,
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }
    )
    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )
```

The message dictionary now looks like:

```python
{
    "role": "user",
    "content": "hola",
    "username": "Alex",
    "timestamp": "12/11/2026 01:23",
}
```

## Sidebar position control

Map display labels to CSS class suffixes:

```python
META_POSITIONS = {
    "Arriba izquierda": "above-left",
    "Arriba derecha": "above-right",
    "Abajo izquierda": "below-left",
    "Abajo derecha": "below-right",
}
```

Render a radio in the sidebar:

```python
st.radio(
    "Posición fecha/hora",
    list(META_POSITIONS),
    index=list(META_POSITIONS).index("Arriba derecha"),
    key="meta_corner_v2",
    help="Dónde mostrar el nombre, la fecha y la hora de cada mensaje.",
)
```

`index=...` makes **Arriba derecha** the default. The `meta_corner_v2` key is
intentional: changing the widget key once resets any stale value from an older
default. If you change the default again and need it to apply to an existing
session, use a new key.

## Render metadata and content together

The metadata and message text must be emitted in the **same** `st.markdown()`
call:

```python
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
```

Why one call instead of two?

Streamlit's message content is a flex container with a `16px` gap between child
elements. If you render the metadata with a separate `st.markdown()` before the
message text, the metadata wrapper is still a flex item even when the metadata
`div` is absolutely positioned and has zero height. The flex gap remains, so the
message text is pushed down by one gap. Combining both into one Markdown call
removes that extra flex item and keeps the text vertically centered.

Escape the user content with `html.escape()` because `unsafe_allow_html=True` is
needed for the metadata `div`.

## CSS

The complete stylesheet used by the app:

```python
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
```

## Why each part works

### The row is the positioning context

```css
[data-testid="stChatMessage"]:has([data-testid="stMenuButton"]) {
  position: relative;
  overflow: visible !important;
}
```

The user `stChatMessage` row is the grey bubble. Making it `position: relative`
gives the absolute metadata and menu a local coordinate system without changing
its width, height, margin, or alignment. This is the key to moving the metadata
without moving the message box.

Do **not** add `width: fit-content`, `align-self`, or margins to this row. Those
change the chat bubble itself. Keep the bubble at its native size and position;
only its absolutely positioned children move.

`overflow: visible` allows metadata and the menu to render outside the row.
Without it, the menu can be clipped or disappear.

### Metadata sits just outside the bubble

```css
.chat-meta {
  position: absolute;
  width: 6.75rem;
  pointer-events: none;
}
```

The four position classes use `top: calc(100% + 6px)` or
`bottom: calc(100% + 6px)`, so the metadata is 6 px outside the bubble on the
selected side. Horizontal alignment is controlled with `left`/`right` and
`text-align`.

The fixed `6.75rem` width creates a predictable gutter for the menu. The current
`Alex · dd/mm/yyyy hh:mm` string is about 6.4 rem wide; 6.75 rem leaves a little
room. If you change the username or timestamp format, re-measure and adjust:

- `.chat-meta` width
- the `right` value of the right-corner metadata
- the `left` value of the left-corner menu

### The menu is positioned on the metadata line

The menu is a separate Streamlit element, so it cannot live inside the metadata
`div`. Instead, position its `stElementContainer` absolutely at the same
vertical line:

```css
[data-testid="stChatMessage"]:has(.chat-meta.pos-above-right)
  [data-testid="stElementContainer"]:has([data-testid="stMenuButton"]) {
  top: auto;
  bottom: calc(100% + 0.5px);
  right: 0.15rem;
}
```

The offsets are asymmetric on purpose. The metadata line is `0.66rem` high,
while the transparent menu button is `1.3rem` high for a comfortable click
target. For above corners, the menu uses `bottom: calc(100% + 0.5px)`; for below
corners it uses `top: calc(100% - 1.5px)`. These values place the visible `≡`
glyph center on the metadata text center; the transparent button box extends
above/below the visible glyph.

If you change the menu font size, line-height, or button height, re-check the
alignment and tune those two offsets. A quick DOM check is to compare the center
of `document.createRange().selectNodeContents(meta)` with the same range on the
menu button.

For left corners, the menu starts at `left: 6.8rem`, which is just after the
fixed-width metadata plus a ~4 px gap. For right corners, the metadata's
`right: 1.4rem` reserves space for the menu, which sits at `right: 0.15rem`.
That produces a consistent ~4 px gap between the timestamp and `≡`.

### Match the menu to the metadata

```css
[data-testid="stChatMessage"] [data-testid="stMenuButton"] button {
  color: var(--st-text-color, #6b5a4c);
  font-size: 0.66rem;
  font-weight: 500;
  opacity: 0.58;
}
```

These values match `.chat-meta`, so the `≡` glyph has the same visual size,
color, weight, and opacity as the timestamp. The button itself remains
`1.3rem` tall with a transparent background so it stays easy to click.

Streamlit renders a chevron next to `st.menu_button`. Hide it so the trigger is
only the `≡` character:

```css
[data-testid="stChatMessage"] [data-testid="stMenuButton"] svg,
[data-testid="stChatMessage"] [data-testid="stMenuButton"] div[aria-hidden="true"] {
  display: none;
}
```

### Render the menu only for user messages

The menu is rendered inside the `message["role"] == "user"` branch. If you render
it for assistant messages too, there is no metadata line to anchor it to, and it
can appear as an extra floating bubble near the previous message. Keeping the
menu user-only avoids that visual artifact.

## Verification checklist

Use a browser with DevTools or Chrome DevTools MCP:

1. Send a message and confirm the metadata appears at the default **Arriba
   derecha** corner.
2. Confirm the metadata is outside the grey bubble, with a small gap.
3. Confirm the message text is vertically centered. It must not be pushed down.
4. Confirm the bubble's bounding rectangle is unchanged compared with a message
   without metadata.
5. Switch through all four radio options:
   - arriba izquierda
   - arriba derecha
   - abajo izquierda
   - abajo derecha
6. Confirm the metadata stays outside the bubble and the menu stays immediately
   to the right of the timestamp.
7. Click `≡` and confirm the menu opens with the expected actions.
8. Select an action and confirm the `st.toast()` appears.
9. Confirm assistant messages have no menu and no extra bubble.

Useful DOM checks:

```js
const rows = [...document.querySelectorAll('[data-testid="stChatMessage"]')];

rows.map((row) => {
  const meta = row.querySelector('.chat-meta');
  const menu = row.querySelector('[data-testid="stMenuButton"]');
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { x: r.x, y: r.y, width: r.width, height: r.height };
  };
  return { message: box(row), meta: box(meta), menu: box(menu) };
});
```

For a right-aligned metadata line, `menu.left - meta.right` should be about
4 px. For a left-aligned line, the same gap should also be about 4 px. The
message row rectangle should remain the native chat-message size.

## Common mistakes

- **Rendering metadata with a separate `st.markdown()`.** Streamlit's flex gap
  pushes the message text down by 16 px. Render metadata and text in one call.
- **Setting width, margin, or alignment on `stChatMessage`.** That moves or
  resizes the chat bubble. Use absolute positioning on the metadata instead.
- **Omitting `position: relative` on the row.** The absolute menu can resolve
  against a different ancestor and render offscreen.
- **Rendering the menu for assistant messages.** It has no metadata anchor and
  can appear as an extra floating bubble.
- **Forgetting to escape user text with `unsafe_allow_html=True`.** Use
  `html.escape()` for the username, timestamp, and message body.
- **Using a gutter that is too wide or too narrow.** Too wide creates the
  "floating menu" look; too narrow makes the menu overlap the timestamp. The
  current values produce about a 4 px gap.
- **Relying on Streamlit test IDs and `:has()` forever.** Re-check
  `stChatMessage`, `stChatMessageContent`, `stElementContainer`, and
  `stMenuButton` after upgrading Streamlit.
- **Changing the radio default without resetting the widget key.** Streamlit
  keeps the old session value. Use a new key when you need the new default to
  apply immediately.

## Relevant project files

- `app.py`: `META_POSITIONS`, `MESSAGE_ACTIONS`, `CHAT_CSS`,
  `handle_message`, sidebar radio, and the chat render loop.
- `docs/centered-chat-input-landing.md`: the centered landing guide that this
  feature builds on.
