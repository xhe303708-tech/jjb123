const EASE = "cubic-bezier(.2,.8,.2,1)";

function smoothstep(x) {
  const t = Math.min(1, Math.max(0, x));
  return t * t * (3 - 2 * t);
}

function modRange(v, n) {
  let r = ((v % n) + n) % n;
  const half = Math.floor(n / 2);
  if (r >= half) r -= n;
  return r;
}

function stepB(r) {
  if (Math.abs(r) < 1) return (r + Math.sin(Math.PI * r) / Math.PI) / 2;
  return Math.sign(r) * 0.5;
}

function artStyle(i) {
  const inks = ["#1F3FB0", "#9E2B22", "#141414", "#315C4E"];
  const a = inks[i % inks.length];
  const b = inks[(i + 1) % inks.length];
  const deg = 28 + (i % 5) * 18;
  return `linear-gradient(${deg}deg, ${a} 0 36%, transparent 36% 58%, ${b} 58% 70%, #E7E1D6 70%)`;
}

export function mountShelf(root, { items, start = 0, fill, onEnter }) {
  const stage = root.querySelector(".stage");
  const shelf = root.querySelector(".shelf");
  const caption = {
    title: root.querySelector("[data-cap='title']"),
    sub: root.querySelector("[data-cap='sub']"),
    year: root.querySelector("[data-cap='year']"),
  };
  const tabs = [...root.querySelectorAll("[data-tab]")];
  const indicator = root.querySelector(".tab-indicator");
  const play = root.querySelector(".play-ring");
  const detail = root.querySelector(".detail");
  const cursor = root.querySelector(".ring-cursor");
  const live = root.querySelector(".caption");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const fine = matchMedia("(pointer: fine)").matches;

  const n = items.length;
  const copies = n >= 4 ? 3 : 1;
  const total = n * copies;
  let s = start + (copies > 1 ? n : 0);
  let T = s;
  let hover = -1;
  const lifts = new Map();
  let tiltX = 0;
  let tiltY = 0;
  let mx = innerWidth / 2;
  let my = innerHeight / 2;
  let cx = mx;
  let cy = my;
  let onCover = false;
  let open = false;
  let dragging = false;
  let dragMoved = false;
  let dragX = 0;
  let dragT = 0;
  let wheelTimer = 0;
  let active = -1;
  let last = performance.now();
  let raf = 0;
  let springK = 5.2;

  const tapes = [];
  stage.innerHTML = "";
  for (let c = 0; c < copies; c++) {
    items.forEach((item, i) => {
      const v = c * n + i;
      const el = document.createElement("div");
      el.className = "tape";
      el.dataset.v = String(v);
      el.innerHTML = `
        <div class="face sp">
          <span class="sp-index">${String(i + 1).padStart(2, "0")}</span>
          <span class="sp-title"></span>
          <span class="sp-brand">课笺</span>
        </div>
        <div class="face cv">
          <span class="cv-kicker"></span>
          <span class="cv-title"></span>
          <span class="cv-art"></span>
          <span class="cv-badge">册</span>
        </div>`;
      el.querySelector(".sp-title").textContent = item.spine || item.title;
      el.querySelector(".cv-kicker").textContent = item.kicker || "KEJIAN";
      el.querySelector(".cv-title").textContent = item.title;
      el.querySelector(".cv-art").style.background = artStyle(i);
      el.querySelector(".cv-badge").textContent = item.badge || "册";
      stage.appendChild(el);
      tapes.push(el);
      el.addEventListener("pointerenter", () => { hover = v; });
      el.addEventListener("pointerleave", () => { if (hover === v) hover = -1; });
      el.addEventListener("click", (event) => {
        if (dragMoved) return;
        const r = Number(el.dataset.r || 0);
        if (Math.abs(r) < 0.5) openDetail();
        else T = Math.round(T + r);
        event.stopPropagation();
      });
    });
  }

  function measure() {
    const probe = root.querySelector(".h-probe");
    const H = probe ? probe.getBoundingClientRect().height : Math.min(innerHeight * 0.46, innerWidth * 0.31);
    const ws = H * 142 / 840;
    const d = H * 474 / 900;
    const gap = H * 0.03;
    stage.style.setProperty("--ws", ws + "px");
    stage.style.setProperty("--d", d + "px");
    stage.style.setProperty("--H", H + "px");
    return { H, ws, d, gap };
  }

  function setCaption(item, dir) {
    const next = [
      [caption.title, item.title],
      [caption.sub, item.sub || ""],
      [caption.year, item.year || ""],
    ];
    next.forEach(([mask, text]) => {
      if (!mask) return;
      if (reduce) {
        mask.textContent = text;
        return;
      }
      const span = document.createElement("span");
      span.textContent = text;
      mask.appendChild(span);
      const old = [...mask.children].slice(0, -1);
      span.animate(
        [{ transform: `translateY(${dir * 105}%)` }, { transform: "translateY(0)" }],
        { duration: 650, easing: EASE, fill: "both" }
      );
      old.forEach((node) => {
        const anim = node.animate(
          [{ transform: "translateY(0)" }, { transform: `translateY(${-dir * 105}%)` }],
          { duration: 650, easing: EASE, fill: "both" }
        );
        anim.onfinish = () => node.remove();
      });
    });
    if (live) live.setAttribute("aria-label", item.title);
    moveTab(item.cat);
  }

  function moveTab(cat) {
    const button = tabs.find((tab) => tab.dataset.tab === cat);
    if (!button || !indicator) return;
    indicator.style.width = button.offsetWidth + "px";
    indicator.style.transform = `translateX(${button.offsetLeft}px)`;
    tabs.forEach((tab) => tab.classList.toggle("is-on", tab === button));
  }

  function frame(now) {
    const dt = Math.min(0.05, (now - last) / 1000);
    last = now;
    const k = reduce ? 80 : springK;
    s += (T - s) * (1 - Math.exp(-k * dt));
    if (Math.abs(T - s) < 1e-4) s = T;
    if (copies > 1 && s > n * 4) { s -= n; T -= n; }
    if (copies > 1 && s < -n) { s += n; T += n; }

    const { H, ws, d, gap } = measure();
    const index = ((Math.round(s) % n) + n) % n;
    if (index !== active) {
      const dir = Math.sign(T - s) || 1;
      active = index;
      setCaption(items[index], dir);
    }

    const shelfRect = shelf.getBoundingClientRect();
    const cyShelf = shelfRect.top + shelfRect.height / 2;
    const settled = Math.abs(T - s) < 0.3 && !open;
    const coverHit = settled && Math.abs(mx - innerWidth / 2) < d * 0.55 && Math.abs(my - cyShelf) < H * 0.55;
    onCover = coverHit;
    const targetY = coverHit ? ((mx - innerWidth / 2) / (d * 0.55)) * 9 : ((mx - innerWidth / 2) / innerWidth) * 5;
    const targetX = coverHit ? -((my - cyShelf) / (H / 2)) * 6 : 0;
    const tiltK = 1 - Math.exp(-7 * dt);
    tiltX += (targetX - tiltX) * tiltK;
    tiltY += (targetY - tiltY) * tiltK;

    tapes.forEach((el) => {
      const v = Number(el.dataset.v);
      const r = modRange(v - s, total);
      el.dataset.r = r.toFixed(3);
      const x = r * (ws + gap) + (d - ws + 1.6 * gap) * stepB(r);
      if (Math.abs(x) > innerWidth / 2 + d * 1.5) {
        el.style.visibility = "hidden";
        return;
      }
      el.style.visibility = "visible";
      const o = smoothstep(Math.max(0, 1 - Math.abs(r)));
      let lift = lifts.get(v) || 0;
      const liftTarget = hover === v && Math.abs(r) > 0.5 ? 1 : 0;
      lift += (liftTarget - lift) * (reduce ? 1 : 1 - Math.exp(-12 * dt));
      lifts.set(v, lift);
      const z = o * 0.2 * H;
      const y = -o * 0.025 * H - lift * 0.045 * H;
      const rotY = -90 * o + tiltY * o;
      const rotX = tiltX * o;
      const rotZ = -4.5 * o;
      el.style.zIndex = String(Math.round(100 - Math.abs(r) * 4));
      el.style.transform = `translate3d(${x}px, ${y}px, ${z}px) rotateZ(${rotZ}deg) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
      const sp = el.querySelector(".sp");
      const cv = el.querySelector(".cv");
      sp.style.setProperty("--shade", String(o * 0.55));
      cv.style.setProperty("--shade", String((1 - o) * 0.5));
    });

    if (play) {
      const pop = open ? 0 : smoothstep(Math.max(0, 1 - Math.abs(T - s) * 3));
      play.style.transform = `translate(-50%, -50%) scale(${pop})`;
      play.style.left = (innerWidth / 2 - d * 0.5 - 6) + "px";
      play.style.top = (cyShelf + H * 0.36) + "px";
    }

    if (cursor && fine) {
      cx += (mx - cx) * (1 - Math.exp(-16 * dt));
      cy += (my - cy) * (1 - Math.exp(-16 * dt));
      cursor.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
      const overSpine = hover >= 0 && !onCover;
      const overBtn = document.elementFromPoint(mx, my)?.closest("button, a");
      cursor.classList.toggle("is-open", onCover && !open);
      cursor.classList.toggle("is-spine", overSpine && !onCover && !open);
      cursor.classList.toggle("is-btn", !!overBtn && !onCover);
    }
    raf = requestAnimationFrame(frame);
  }

  function openDetail() {
    if (open) return;
    const item = items[active];
    if (!item || !detail) {
      onEnter?.(item);
      return;
    }
    T = Math.round(T);
    s = T;
    fillDetail(item);
    const cover = [...tapes].find((el) => Math.abs(Number(el.dataset.r)) < 0.2)?.querySelector(".cv");
    const rect = cover?.getBoundingClientRect();
    detail.hidden = false;
    detail.classList.add("is-open");
    open = true;
    if (!rect || reduce) {
      detail.style.clipPath = "inset(0 0 0 0 round 0)";
      detail.style.transform = "none";
      return;
    }
    const top = rect.top;
    const right = innerWidth - rect.right;
    const bottom = innerHeight - rect.bottom;
    const left = rect.left;
    detail.style.transformOrigin = `${rect.left + rect.width / 2}px ${rect.top + rect.height / 2}px`;
    detail.animate(
      [
        { clipPath: `inset(${top}px ${right}px ${bottom}px ${left}px round 3px)`, transform: "rotate(-4.5deg)" },
        { clipPath: "inset(0 0 0 0 round 0)", transform: "rotate(0deg)" },
      ],
      { duration: 1050, easing: "cubic-bezier(.76,0,.18,1)", fill: "both" }
    );
    detail.querySelectorAll("[data-rise]").forEach((line, i) => {
      line.animate(
        [{ transform: "translateY(110%)" }, { transform: "translateY(0)" }],
        { duration: 900, delay: 620 + i * 75, easing: EASE, fill: "both" }
      );
    });
    bleed();
  }

  function fillDetail(item) {
    fill?.(item, detail);
    detail.querySelectorAll(".ink circle").forEach((circle) => circle.setAttribute("r", "0"));
  }

  function bleed() {
    const circles = [...detail.querySelectorAll(".ink circle")];
    const t0 = performance.now();
    const delays = [0, 120, 220, 300, 360, 420, 180];
    const loop = (now) => {
      circles.forEach((circle, i) => {
        const p = Math.min(1, Math.max(0, (now - t0 - delays[i]) / 1250));
        const eased = 1 - (1 - p) ** 3;
        circle.setAttribute("r", String(reduce ? 720 : eased * 720));
      });
      if (now - t0 < 2400 && !reduce) requestAnimationFrame(loop);
    };
    if (reduce) circles.forEach((circle) => circle.setAttribute("r", "720"));
    else requestAnimationFrame(loop);
  }

  function closeDetail() {
    if (!open) return;
    const cover = [...tapes].find((el) => Math.abs(Number(el.dataset.r)) < 0.2)?.querySelector(".cv");
    const rect = cover?.getBoundingClientRect();
    const done = () => {
      detail.classList.remove("is-open");
      detail.hidden = true;
      open = false;
    };
    if (!rect || reduce) {
      done();
      return;
    }
    const anim = detail.animate(
      [
        { clipPath: "inset(0 0 0 0 round 0)", transform: "rotate(0deg)" },
        {
          clipPath: `inset(${rect.top}px ${innerWidth - rect.right}px ${innerHeight - rect.bottom}px ${rect.left}px round 3px)`,
          transform: "rotate(-4.5deg)",
        },
      ],
      { duration: 850, easing: "cubic-bezier(.76,0,.18,1)", fill: "both" }
    );
    anim.onfinish = done;
  }

  function onKey(event) {
    if (event.key === "Escape") closeDetail();
    if (open) return;
    if (event.key === "ArrowRight") T = Math.round(T) + 1;
    if (event.key === "ArrowLeft") T = Math.round(T) - 1;
    if (event.key === "Enter") openDetail();
  }
  function onMove(event) {
    mx = event.clientX;
    my = event.clientY;
  }
  function onWheel(event) {
    if (open) return;
    event.preventDefault();
    const delta = Math.abs(event.deltaX) > Math.abs(event.deltaY) ? event.deltaX : event.deltaY;
    const { ws, gap } = measure();
    T += delta / (ws + gap) * 0.5;
    springK = 5.2;
    clearTimeout(wheelTimer);
    wheelTimer = setTimeout(() => { T = Math.round(T); }, 160);
  }
  function onDown(event) {
    if (open || event.button !== 0) return;
    dragging = true;
    dragMoved = false;
    dragX = event.clientX;
    dragT = T;
    shelf.setPointerCapture?.(event.pointerId);
  }
  function onUp() {
    if (!dragging) return;
    dragging = false;
    if (dragMoved) T = Math.round(T);
    springK = 5.2;
    setTimeout(() => { dragMoved = false; }, 0);
  }
  function onDrag(event) {
    if (!dragging) return;
    const dx = event.clientX - dragX;
    if (Math.abs(dx) > 5) {
      dragMoved = true;
      const { ws, gap } = measure();
      T = dragT - dx / (ws + gap);
      springK = 18;
    }
  }

  root.querySelector(".prev")?.addEventListener("click", () => { T = Math.round(T) - 1; });
  root.querySelector(".next")?.addEventListener("click", () => { T = Math.round(T) + 1; });
  play?.addEventListener("click", openDetail);
  detail?.querySelector(".close-sheet")?.addEventListener("click", closeDetail);
  detail?.querySelector(".enter")?.addEventListener("click", () => onEnter?.(items[active]));
  tabs.forEach((tab) => tab.addEventListener("click", () => {
    const cat = tab.dataset.tab;
    const base = Math.round(s) - ((Math.round(s) % n) + n) % n;
    if (cat === "全部") { T = base; return; }
    const i = items.findIndex((item) => item.cat === cat);
    if (i < 0) return;
    T = base + i;
  }));
  addEventListener("keydown", onKey);
  addEventListener("pointermove", onMove);
  shelf.addEventListener("wheel", onWheel, { passive: false });
  shelf.addEventListener("pointerdown", onDown);
  shelf.addEventListener("pointermove", onDrag);
  shelf.addEventListener("pointerup", onUp);
  raf = requestAnimationFrame(frame);

  return {
    destroy() { cancelAnimationFrame(raf); },
    close: closeDetail,
    current: () => items[active],
  };
}
