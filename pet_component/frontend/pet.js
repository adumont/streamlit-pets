/**
 * Streamlit Pets - frontend renderer.
 *
 * Renders a Codex-compatible sprite atlas (v1: 8x9, v2: 8x11) or the built-in
 * SVG pet when no sprite is supplied. Python sends `data` on every rerun and
 * receives the "poked" trigger when the pet is clicked / activated.
 */

const STATE_ROWS = {
  idle: 0,
  "running-right": 1,
  "walk-right": 1,
  "running-left": 2,
  "walk-left": 2,
  waving: 3,
  wave: 3,
  jumping: 4,
  jump: 4,
  failed: 5,
  sad: 5,
  error: 5,
  waiting: 6,
  wait: 6,
  running: 7,
  working: 7,
  review: 8,
  sleeping: 0,
  sleep: 0,
};

const FRAME_MS = {
  idle: 220,
  "running-right": 90,
  "running-left": 90,
  waving: 130,
  jumping: 110,
  failed: 150,
  waiting: 240,
  running: 120,
  review: 170,
  sleeping: 320,
};

const REACTIONS = [
  "¡Jeje!",
  "¡Otra vez!",
  "Me gusta eso",
  "¡Qué cosquillas!",
  "¡Miau!",
];

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function normalizeLook(value) {
  if (Array.isArray(value)) {
    return {
      x: clamp(Number(value[0]) || 0, -1, 1),
      y: clamp(Number(value[1]) || 0, -1, 1),
    };
  }
  if (value && typeof value === "object") {
    return {
      x: clamp(Number(value.x) || 0, -1, 1),
      y: clamp(Number(value.y) || 0, -1, 1),
    };
  }
  return { x: 0, y: 0 };
}

function detectFrameCounts(image, columns, rows, frameWidth, frameHeight) {
  const scratch = document.createElement("canvas");
  scratch.width = frameWidth;
  scratch.height = frameHeight;
  const context = scratch.getContext("2d", { willReadFrequently: true });
  const counts = [];

  for (let row = 0; row < rows; row += 1) {
    let populated = 0;
    for (let column = 0; column < columns; column += 1) {
      context.clearRect(0, 0, frameWidth, frameHeight);
      context.drawImage(
        image,
        column * frameWidth,
        row * frameHeight,
        frameWidth,
        frameHeight,
        0,
        0,
        frameWidth,
        frameHeight,
      );
      const pixels = context.getImageData(0, 0, frameWidth, frameHeight).data;
      let opaque = 0;
      for (let index = 3; index < pixels.length; index += 4) {
        if (pixels[index] > 8) {
          opaque += 1;
          if (opaque > 40) break;
        }
      }
      if (opaque > 40) populated += 1;
    }
    counts.push(Math.max(1, populated));
  }

  return counts;
}

export default function renderPet(component) {
  const { parentElement, data, setTriggerValue } = component;
  const root = parentElement.querySelector(".pet-root");
  if (!root) return undefined;

  if (typeof root.__petCleanup === "function") {
    root.__petCleanup();
    root.__petCleanup = null;
  }

  const payload = data && typeof data === "object" ? data : {};
  const stage = root.querySelector(".pet-stage");
  const bubble = root.querySelector(".pet-bubble");
  const fx = root.querySelector(".pet-fx");
  const canvas = root.querySelector(".pet-canvas");
  const size = clamp(Number(payload.size) || 220, 120, 420);
  const baseLook = normalizeLook(payload.look);
  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  const runtime = {
    data: payload,
    stage,
    bubble,
    fx,
    canvas,
    size,
    look: { ...baseLook },
    sprite: null,
    ctx: null,
    raf: 0,
    timers: new Set(),
    destroyed: false,
    reducedMotion,
  };

  root.style.setProperty("--pet-size", `${size}px`);
  root.dataset.state = String(payload.state || "idle");
  root.dataset.pixelated = payload.pixelated === false ? "false" : "true";
  root.classList.toggle("floating", Boolean(payload.floating));
  root.style.setProperty("--look-x", baseLook.x.toFixed(3));
  root.style.setProperty("--look-y", baseLook.y.toFixed(3));

  const showBubble = (text, timeout = 0) => {
    if (runtime.messageTimer) {
      clearTimeout(runtime.messageTimer);
      runtime.messageTimer = 0;
    }
    if (text) {
      bubble.textContent = String(text);
      bubble.classList.add("show");
    } else {
      bubble.classList.remove("show");
    }

    if (timeout > 0) {
      runtime.messageTimer = setTimeout(() => {
        const baseMessage = String(runtime.data.message || "");
        if (baseMessage) {
          bubble.textContent = baseMessage;
          bubble.classList.add("show");
        } else {
          bubble.classList.remove("show");
        }
      }, timeout);
    }
  };

  showBubble(payload.message);

  const setLook = (look) => {
    runtime.look = look;
    root.style.setProperty("--look-x", look.x.toFixed(3));
    root.style.setProperty("--look-y", look.y.toFixed(3));
  };

  const onPointerMove = (event) => {
    const rect = stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    setLook({
      x: clamp(((event.clientX - rect.left) / rect.width - 0.5) * 2, -1, 1),
      y: clamp(((event.clientY - rect.top) / rect.height - 0.5) * 2, -1, 1),
    });
  };

  const onPointerLeave = () => setLook({ ...baseLook });

  const spawnHearts = () => {
    for (let index = 0; index < 6; index += 1) {
      const heart = document.createElement("span");
      heart.className = "pet-heart";
      heart.textContent = "♥";
      heart.style.left = `${28 + Math.random() * 44}%`;
      heart.style.top = `${38 + Math.random() * 18}%`;
      heart.style.setProperty("--dx", `${(Math.random() - 0.5) * 46}px`);
      heart.style.animationDelay = `${index * 45}ms`;
      fx.appendChild(heart);
      const timer = setTimeout(() => heart.remove(), 1050);
      runtime.timers.add(timer);
    }
  };

  const poke = () => {
    showBubble(REACTIONS[Math.floor(Math.random() * REACTIONS.length)], 1900);
    spawnHearts();
    stage.classList.remove("is-poked");
    // Restart the poke animation even on rapid clicks.
    void stage.offsetWidth;
    stage.classList.add("is-poked");
    if (runtime.pokeTimer) clearTimeout(runtime.pokeTimer);
    runtime.pokeTimer = setTimeout(
      () => stage.classList.remove("is-poked"),
      460,
    );
    setTriggerValue("poked", {
      kind: "poke",
      pet: String(payload.petName || "pet"),
      at: Date.now(),
    });
  };

  const onKeyDown = (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      poke();
    }
  };

  const layoutCanvas = (sprite) => {
    const dpr = Math.min(window.devicePixelRatio || 1, 3);
    const pixelWidth = Math.max(1, Math.round(sprite.fw * dpr));
    const pixelHeight = Math.max(1, Math.round(sprite.fh * dpr));
    if (canvas.width !== pixelWidth || canvas.height !== pixelHeight) {
      canvas.width = pixelWidth;
      canvas.height = pixelHeight;
    }
    canvas.style.height = `${size}px`;
    canvas.style.width = `${((size * sprite.fw) / sprite.fh).toFixed(2)}px`;
    const context = canvas.getContext("2d");
    context.setTransform(dpr, 0, 0, dpr, 0, 0);
    context.imageSmoothingEnabled = payload.pixelated === false;
    runtime.ctx = context;
  };

  const drawFrame = (now) => {
    const sprite = runtime.sprite;
    if (!sprite || !sprite.ready || !runtime.ctx) return;

    const state = String(root.dataset.state || "idle");
    let row = STATE_ROWS[state] ?? 0;
    let lookIndex = -1;

    if (state === "idle" && sprite.rows >= 11) {
      const look = runtime.look;
      if (Math.hypot(look.x, look.y) > 0.12) {
        let angle = (Math.atan2(look.x, -look.y) * 180) / Math.PI;
        angle = (angle + 360) % 360;
        lookIndex = Math.round(angle / 22.5) % 16;
        row = 9 + Math.floor(lookIndex / 8);
      }
    }

    if (row >= sprite.rows) row = 0;
    const frames = sprite.frameCounts[row] || 1;
    const frameDuration = lookIndex >= 0 ? 140 : FRAME_MS[state] || 180;
    const frame = runtime.reducedMotion
      ? 0
      : Math.floor(now / frameDuration) % frames;

    runtime.ctx.clearRect(0, 0, sprite.fw, sprite.fh);
    runtime.ctx.drawImage(
      sprite.img,
      frame * sprite.fw,
      row * sprite.fh,
      sprite.fw,
      sprite.fh,
      0,
      0,
      sprite.fw,
      sprite.fh,
    );
  };

  const startLoop = () => {
    if (runtime.raf || !runtime.sprite || !runtime.sprite.ready) return;
    if (runtime.reducedMotion) {
      drawFrame(0);
      return;
    }
    const tick = (now) => {
      if (runtime.destroyed) return;
      drawFrame(now);
      runtime.raf = requestAnimationFrame(tick);
    };
    runtime.raf = requestAnimationFrame(tick);
  };

  const setupSprite = (spriteData) => {
    const url = String(spriteData.dataUrl || "");
    if (!url) {
      root.classList.remove("using-sprite");
      return;
    }

    const cached = root.__spriteCache;
    if (cached && cached.dataUrl === url && cached.ready) {
      runtime.sprite = cached;
      layoutCanvas(cached);
      startLoop();
      return;
    }

    const sprite = {
      dataUrl: url,
      fw: Number(spriteData.frameWidth) || 192,
      fh: Number(spriteData.frameHeight) || 208,
      img: new Image(),
      ready: false,
      rows: 0,
      frameCounts: [],
    };

    sprite.img.onload = () => {
      if (runtime.destroyed) return;
      sprite.rows = Math.max(
        1,
        Math.round(sprite.img.naturalHeight / sprite.fh),
      );
      sprite.frameCounts = detectFrameCounts(
        sprite.img,
        8,
        sprite.rows,
        sprite.fw,
        sprite.fh,
      );
      sprite.ready = true;
      root.__spriteCache = sprite;
      layoutCanvas(sprite);
      startLoop();
    };
    sprite.img.onerror = () => root.classList.remove("using-sprite");
    sprite.img.src = url;

    runtime.sprite = sprite;
  };

  stage.addEventListener("pointermove", onPointerMove);
  stage.addEventListener("pointerleave", onPointerLeave);
  stage.addEventListener("click", poke);
  stage.addEventListener("keydown", onKeyDown);

  const spriteData =
    payload.sprite && typeof payload.sprite === "object" ? payload.sprite : null;
  const useSprite = Boolean(spriteData && spriteData.dataUrl);
  root.classList.toggle("using-sprite", useSprite);
  if (useSprite) {
    setupSprite(spriteData);
  } else {
    root.__spriteCache = null;
  }

  const cleanup = () => {
    runtime.destroyed = true;
    if (runtime.raf) cancelAnimationFrame(runtime.raf);
    runtime.raf = 0;
    if (runtime.messageTimer) clearTimeout(runtime.messageTimer);
    if (runtime.pokeTimer) clearTimeout(runtime.pokeTimer);
    runtime.timers.forEach((timer) => clearTimeout(timer));
    runtime.timers.clear();
    stage.removeEventListener("pointermove", onPointerMove);
    stage.removeEventListener("pointerleave", onPointerLeave);
    stage.removeEventListener("click", poke);
    stage.removeEventListener("keydown", onKeyDown);
    stage.classList.remove("is-poked");
    fx.querySelectorAll(".pet-heart").forEach((heart) => heart.remove());
    root.__petCleanup = null;
  };

  root.__petCleanup = cleanup;
  return cleanup;
}
