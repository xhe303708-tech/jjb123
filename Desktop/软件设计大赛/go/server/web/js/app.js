const room = document.querySelector("#room");
const nav = document.querySelector("#nav");
const links = [
  ["/app/home", "今天"],
  ["/app/words", "单词"],
  ["/app/speak", "口语"],
  ["/app/chat", "助手"],
  ["/app/profile", "我的"],
];
nav.innerHTML = links.map(([href, label]) => `<a class="${location.pathname === href ? "on" : ""}" href="${href}">${label}</a>`).join("");

const days = ["一", "二", "三", "四", "五", "六", "日"];
async function api(url, options) {
  const res = await fetch(url, options);
  const body = await res.json().catch(() => ({}));
  if (res.status === 401) location.href = "/login?next=" + location.pathname;
  if (!res.ok) throw new Error(body.error || "没有完成");
  return body;
}
function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}
function md(text) {
  const safe = esc(text);
  const bits = safe.split("```");
  return bits.map((bit, i) => {
    if (i % 2 === 1) return `<pre><code>${bit.replace(/^\w*\n/, "")}</code></pre>`;
    return bit.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>");
  }).join("");
}
function renderEvent(ev, done) {
  const payload = JSON.parse(ev.payload);
  if (ev.type === "user_message") return `<div class="dsh-msg user">${esc(payload.text)}</div>`;
  if (ev.type === "assistant_message") {
    const think = payload.thinking ? `<details><summary>思考</summary><p>${esc(payload.thinking)}</p></details>` : "";
    return `<div class="dsh-msg">${think}${md(payload.text || "")}</div>`;
  }
  if (ev.type === "assistant_attempt") return `<p class="err">${esc(payload.error || "没有完成")}</p>`;
  if (ev.type === "tool_call") {
    const waiting = !done.has(payload.call_id);
    const buttons = waiting ? `<div class="actions"><button class="judge" data-tool="${ev.id}" data-accept="1" type="button">确认</button><button class="lbl-btn" data-tool="${ev.id}" data-accept="0" type="button">取消</button></div>` : `<span class="lbl">已处理</span>`;
    return `<div class="dsh-tool"><b>${esc(payload.name)}</b><pre>${esc(JSON.stringify(payload.args))}</pre>${buttons}</div>`;
  }
  if (ev.type === "tool_result") return `<div class="dsh-msg">${esc(payload.output)}</div>`;
  return "";
}
async function readSSE(res, onEvent) {
  const reader = res.body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let cut;
    while ((cut = buf.indexOf("\n\n")) >= 0) {
      const block = buf.slice(0, cut);
      buf = buf.slice(cut + 2);
      let event = "message";
      let data = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data += line.slice(5).trim();
      }
      if (data) onEvent(event, JSON.parse(data));
    }
  }
}

const pages = {
  async "/app/home"() {
    const data = await api("/api/home");
    const faces = { words: "🍃", speak: "🎤", schedule: "🗓", notes: "📝", plan: "🧲", lab: "🧪", career: "🚇", diary: "📰", class: "🧩", atlas: "🏷" };
    room.innerHTML = `
      <section class="room">
        <div class="hero-pill">
          <img alt="" src="https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/726b168c-da47-4682-a255-cc3e02f89bae.jpg">
          <div>
            <div class="lbl">${data.locked ? "先说一句，门才全开" : "今天的小路"}</div>
            <h1>${esc(data.user.name)}，先走亮着的一关。</h1>
          </div>
        </div>
        <ol class="path">${data.doors.map((d) => `<li><a class="node${d.Lit ? "" : " off"}" href="${d.Href}"><span class="bubble">${faces[d.ID] || "✦"}</span><span><b>${esc(d.Title)}</b><small>${esc(d.Note)}</small></span></a></li>`).join("")}</ol>
      </section>`;
  },
  async "/app/profile"() {
    const s = await api("/api/profile");
    room.innerHTML = `
      <section class="room">
        <div class="seal-mark">${esc(s.name.slice(0, 1))}</div>
        <h1>${esc(s.name)}</h1>
        <p class="lbl">${esc(s.email)}</p>
        <div class="stats">
          <div>连续 <strong>${s.streak}</strong> 天</div>
          <div>过关 <strong>${s.known}</strong></div>
          <div>抓住假动作 <strong>${s.caught}</strong></div>
          <div class="trust">可信度 ${Array.from({ length: 5 }, (_, i) => `<i class="${i < s.trust ? "on" : ""}"></i>`).join("")}</div>
        </div>
        <p>正在背的一册：${esc(s.deck)}</p>
        <a class="enter" href="/app/settings" style="width:max-content">设置</a>
      </section>`;
  },
  async "/app/settings"() {
    const s = await api("/api/profile");
    const decks = (await api("/api/decks")).decks;
    room.innerHTML = `
      <section class="room">
        <h1>设置</h1>
        <form id="set" class="card" style="width:min(560px,100%)">
          <label>姓名<input name="name" value="${esc(s.name)}"></label>
          <label>词册<select name="deck">${decks.map((d) => `<option ${d === s.deck ? "selected" : ""}>${esc(d)}</option>`).join("")}</select></label>
          <label class="check"><input type="checkbox" name="freeze" ${s.freeze ? "checked" : ""}> 连胜保护，断一天不归零</label>
          <label class="check"><input type="checkbox" name="leaderboard" ${s.leaderboard ? "checked" : ""}> 参加每周经验排行</label>
          <label class="check"><input type="checkbox" name="doorkeeper" ${s.doorkeeper ? "checked" : ""}> 守门：第一句口语没说完，别的门不亮</label>
          <button class="enter" type="submit">保存</button>
        </form>
        <form id="pw" class="card" style="width:min(560px,100%)">
          <h2 style="font-family:var(--serif);font-weight:400;margin:0">修改密码</h2>
          <label>原来的密码<input name="old" type="password" required></label>
          <label>新密码<input name="next" type="password" minlength="8" required></label>
          <button class="enter" type="submit">更新密码</button>
          <p class="err" id="pwerr"></p>
        </form>
        <button class="lbl-btn" id="out" type="button">退出登录</button>
        <form id="imp" class="card" style="width:min(560px,100%)">
          <h2 style="font-family:var(--serif);font-weight:400;margin:0">导入一册单词</h2>
          <p>每行：单词,音标,中文,例句。可以导入四六级、雅思或你自己的表。</p>
          <label>放入哪一册<input name="deck" value="日常"></label>
          <textarea name="body" placeholder="cascade,/kæˈskeɪd/,倾泻,Water cascaded down."></textarea>
          <button class="enter" type="submit">导入</button>
        </form>
      </section>`;
    room.querySelector("#set").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      await api("/api/settings", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
        name: fd.get("name"), deck: fd.get("deck"),
        freeze: fd.get("freeze") === "on", leaderboard: fd.get("leaderboard") === "on", doorkeeper: fd.get("doorkeeper") === "on",
      }) });
      location.reload();
    };
    room.querySelector("#pw").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      try {
        await api("/api/password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ old: fd.get("old"), next: fd.get("next") }) });
        room.querySelector("#pwerr").textContent = "已经更新";
      } catch (err) { room.querySelector("#pwerr").textContent = err.message; }
    };
    room.querySelector("#out").onclick = async () => { await api("/api/logout", { method: "POST" }); location.href = "/"; };
    room.querySelector("#imp").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const body = await api("/api/words/import", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ deck: fd.get("deck"), body: fd.get("body") }) });
      alert("导入了 " + body.count + " 个词");
    };
  },
  async "/app/words"() {
    const deck = new URLSearchParams(location.search).get("deck") || "";
    const decks = (await api("/api/decks")).decks;
    const data = await api("/api/words" + (deck ? "?deck=" + encodeURIComponent(deck) : ""));
    const words = data.words.length ? data.words : [{ id: 0, term: "空", phonetic: "", meaning: "这一册今天没有到期的词", example: "换一册，或在设置里导入。", deck: deck || "词册" }];
    let i = 0;
    const draw = () => {
      const w = words[i];
      room.innerHTML = `
        <section class="room word-stage">
          <div class="decks">${decks.map((d) => `<a class="${d === (w.deck || deck) ? "on" : ""}" href="/app/words?deck=${encodeURIComponent(d)}">${esc(d)}</a>`).join("")}</div>
          <button class="flip" id="flip" type="button" aria-label="翻转卡片">
            <div class="flip-inner">
              <div class="face"><span class="lbl">${esc(w.deck || "")}</span><strong>${esc(w.term)}</strong><em>${esc(w.phonetic)}</em></div>
              <div class="face back"><strong style="font-size:36px">${esc(w.meaning)}</strong><p>${esc(w.example)}</p></div>
            </div>
          </button>
          <div class="actions">
            <button class="judge" data-claim="again" type="button">再记</button>
            <button class="judge" data-claim="fake" type="button">这是假的</button>
            <button class="judge" data-claim="know" type="button">会了</button>
          </div>
          <p class="err" id="judge-msg">${i + 1} / ${words.length} · 点卡片翻转</p>
        </section>`;
      const card = room.querySelector("#flip");
      card.onmousemove = (event) => {
        const r = card.getBoundingClientRect();
        const x = (event.clientX - r.left) / r.width - 0.5;
        const y = (event.clientY - r.top) / r.height - 0.5;
        if (!card.classList.contains("is-back")) card.style.transform = `rotateY(${x * 12}deg) rotateX(${-y * 8}deg)`;
      };
      card.onmouseleave = () => { card.style.transform = ""; };
      card.onclick = () => card.classList.toggle("is-back");
      room.querySelector(".actions").onclick = async (event) => {
        const button = event.target.closest("[data-claim]");
        if (!button || !w.id) return;
        const body = await api("/api/words/judge", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: w.id, claim: button.dataset.claim }) });
        room.querySelector("#judge-msg").textContent = body.message;
        i = (i + 1) % words.length;
        setTimeout(draw, 350);
      };
    };
    draw();
  },
  async "/app/schedule"() {
    const data = await api("/api/schedule");
    const cols = days.map((name, i) => {
      const weekday = i + 1;
      const items = data.courses.filter((c) => c.weekday === weekday);
      return `<div class="day${items.length >= 3 ? " narrow" : ""}${weekday === data.today ? " today" : ""}"><span class="lbl">周${name}</span>${items.map((c) => `<div class="class-chip${c.stamped ? "" : " raw"}">${esc(c.name)}<br><button class="lbl" data-move="${c.id}" data-day="${weekday === 7 ? 1 : weekday + 1}" type="button">挪到下一天</button></div>`).join("")}</div>`;
    }).join("");
    room.innerHTML = `<section class="room"><div class="lbl kicker">走廊</div><h1>课表</h1><p>同一天有三门及以上，走廊变窄。没盖章的格子还留着照片的颗粒。</p><div class="week">${cols}</div>
      <form id="add" class="row"><input name="name" placeholder="课名" required><select name="weekday">${days.map((d, i) => `<option value="${i + 1}">周${d}</option>`).join("")}</select><label class="check"><input type="checkbox" name="stamped" checked> 我来盖章</label><button class="enter" type="submit">放入</button></form>
      <label class="check">照片 <input type="file" id="photo" accept="image/*"></label><img id="shot" alt="" style="max-width:280px;display:none"></section>`;
    room.querySelector("#add").onsubmit = async (e) => {
      e.preventDefault();
      const fd = new FormData(e.target);
      await api("/api/schedule", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ name: fd.get("name"), weekday: Number(fd.get("weekday")), stamped: fd.get("stamped") === "on" }) });
      location.reload();
    };
    room.querySelectorAll("[data-move]").forEach((btn) => btn.onclick = async () => {
      await api("/api/schedule/move", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: Number(btn.dataset.move), weekday: Number(btn.dataset.day) }) });
      location.reload();
    });
    room.querySelector("#photo").onchange = (e) => {
      const file = e.target.files[0];
      if (!file) return;
      const img = room.querySelector("#shot");
      img.src = URL.createObjectURL(file);
      img.style.display = "block";
    };
  },
  async "/app/notes"() {
    const data = await api("/api/notes");
    const fake = "银行家算法通过预分配避免死锁。";
    room.innerHTML = `<section class="room"><div class="lbl kicker">雾</div><h1>笔记</h1>
      <textarea id="note">${esc(data.body)}</textarea>
      <div class="row"><button class="enter" id="save" type="button">落地</button><button class="lbl-btn" id="tear" type="button">撕掉助手抄来的一句</button></div>
      <p id="note-msg"></p>
      <div class="fog" id="fog"></div>
      <p class="sentence">助手抄来：${esc(fake)}</p></section>`;
    const paint = (sentences) => {
      room.querySelector("#fog").innerHTML = (sentences || []).map((s) => `<div class="sentence">${esc(s)}</div>`).join("") || "<p>还没有句子。</p>";
    };
    paint(data.sentences);
    room.querySelector("#save").onclick = async () => {
      const body = await api("/api/notes", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ body: room.querySelector("#note").value }) });
      paint(body.sentences);
    };
    room.querySelector("#tear").onclick = async () => {
      const body = await api("/api/notes/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sentence: fake }) });
      room.querySelector("#note-msg").textContent = body.ok ? "这句居然在笔记里。" : "撕掉了。" + body.reason;
    };
  },
  async "/app/speak"() {
    room.innerHTML = `<section class="room"><div class="lbl kicker">开口</div><h1>Today I open one door.</h1>
      <p>跟读这一句。说完，守门会放开今晚的房间。也可以打字。</p>
      <form id="say" class="row"><input name="line" placeholder="Today I open one door." required><button class="enter" type="submit">这句我说了</button><button class="lbl-btn" id="mic" type="button">麦克风</button></form>
      <p id="say-msg"></p></section>`;
    const input = room.querySelector("input");
    room.querySelector("#say").onsubmit = async (e) => {
      e.preventDefault();
      const body = await api("/api/speak", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ line: input.value }) });
      room.querySelector("#say-msg").textContent = body.message;
    };
    room.querySelector("#mic").onclick = () => {
      const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!Rec) { room.querySelector("#say-msg").textContent = "这台浏览器没有语音识别，直接打字。"; return; }
      const rec = new Rec();
      rec.lang = "en-US";
      rec.onresult = (ev) => { input.value = ev.results[0][0].transcript; };
      rec.start();
    };
  },
  async "/app/plan"() {
    const data = await api("/api/plan");
    const todayItems = data.items.filter((item) => item.day === data.today);
    room.innerHTML = `<section class="room"><div class="lbl kicker">白板</div><h1>计划</h1>
      <div class="magnets">${data.items.map((item) => `<div class="magnet${todayItems.length >= 3 && item.day === data.today ? " fall" : ""}"><strong>${esc(item.title)}</strong><div class="lbl">${esc(item.day)}</div><button class="lbl" data-shift="${item.id}" type="button">让后面的你拿走</button></div>`).join("") || "<p>白板还是空的。</p>"}</div>
      <form id="add" class="row"><input name="title" placeholder="今晚要做的一件" required><button class="enter" type="submit">贴上</button></form></section>`;
    room.querySelector("#add").onsubmit = async (e) => {
      e.preventDefault();
      await api("/api/plan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: new FormData(e.target).get("title"), day: data.today }) });
      location.reload();
    };
    room.querySelectorAll("[data-shift]").forEach((btn) => btn.onclick = async () => {
      await api("/api/plan/shift", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id: Number(btn.dataset.shift) }) });
      location.reload();
    });
  },
  async "/app/lab"() {
    room.innerHTML = `<section class="room"><div class="lbl kicker">实验台</div><h1>把数字放回格子</h1>
      <div class="bench"><textarea id="rec">n,time_ms
1,12
2,18
3,21
4,30
5,15</textarea><textarea id="con" placeholder="平均耗时 12.4 毫秒，样本数为 5。"></textarea></div>
      <button class="enter" id="go" type="button">核对</button>
      <div id="tubes"></div><p id="partner"></p><button class="lbl-btn" id="catch" type="button" hidden>抓住同桌报错的数</button></section>`;
    room.querySelector("#go").onclick = async () => {
      const body = await api("/api/lab/check", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ record: room.querySelector("#rec").value, conclusion: room.querySelector("#con").value }) });
      room.querySelector("#tubes").innerHTML = (body.hits || []).map((h) => `<span class="tube ${h.verdict === "成立" ? "ok" : "bad"}">${esc(h.value)} ${esc(h.verdict)}</span>`).join("") + `<p class="lbl">样本 ${body.count} · 平均 ${body.mean} · 最大 ${body.max}</p>`;
      room.querySelector("#partner").textContent = body.partnerLine;
      room.querySelector("#catch").hidden = false;
    };
    room.querySelector("#catch").onclick = async () => {
      const body = await api("/api/catch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: "lab" }) });
      room.querySelector("#partner").textContent = "抓住了。可信度 " + body.trust;
    };
  },
  async "/app/career"() {
    const data = await api("/api/career");
    room.innerHTML = `<section class="room"><div class="lbl kicker">地铁</div><h1>先修没盖章，闸机不开</h1>
      <div class="line">${data.stops.map((s) => `<div class="stop${s.open ? "" : " lock"}"><strong>${esc(s.name)}</strong><div class="lbl">${s.need ? "需要 " + esc(s.need) : "起点"} · ${s.hours} 学时</div>${s.ticket ? `<button class="lbl-btn" id="reject" type="button">退回这张票</button>` : `<button class="lbl" data-course="${esc(s.name)}" data-on="${s.done ? "0" : "1"}" type="button">${s.done ? "撕掉章" : "盖章"}</button>`}</div>`).join("")}</div>
      <p id="cmsg"></p></section>`;
    room.querySelectorAll("[data-course]").forEach((btn) => btn.onclick = async () => {
      try {
        await api("/api/career", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ course: btn.dataset.course, on: btn.dataset.on === "1" }) });
        location.reload();
      } catch (err) { room.querySelector("#cmsg").textContent = err.message; }
    });
    room.querySelector("#reject").onclick = async () => {
      const body = await api("/api/career/reject", { method: "POST" });
      room.querySelector("#cmsg").textContent = body.message;
    };
  },
  async "/app/diary"() {
    const data = await api("/api/diary");
    room.innerHTML = `<section class="room"><article class="paper-news"><div class="lbl">课笺早报 · 今天</div><h2>只印过关的句子</h2>
      ${(data.lines.length ? data.lines : ["今天还没有一句过关。"]).map((line) => `<p>${esc(line)}</p>`).join("")}
      <div class="blank">${esc(data.blank)}</div>
      <p class="credit">${esc(data.correction)}</p></article></section>`;
  },
  async "/app/class"() {
    const pieces = ["互斥", "占有且等待", "不可剥夺", "银行家算法"];
    room.innerHTML = `<section class="room"><div class="lbl kicker">一桌</div><h1>哪一块不在原文里</h1>
      <p>原文：死锁的四个必要条件是互斥、占有且等待、不可剥夺和循环等待。</p>
      <div class="pieces">${pieces.map((p) => `<button class="piece" type="button">${esc(p)}</button>`).join("")}</div>
      <p id="cmsg"></p></section>`;
    room.querySelectorAll(".piece").forEach((btn) => btn.onclick = async () => {
      if (btn.textContent !== "银行家算法") {
        room.querySelector("#cmsg").textContent = "这块在原文里。";
        return;
      }
      const body = await api("/api/catch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ kind: "class" }) });
      room.querySelector("#cmsg").textContent = "这一块被挡住了。可信度 " + body.trust;
    });
  },
  async "/app/atlas"() {
    const s = await api("/api/profile");
    room.innerHTML = `<section class="room"><div class="lbl kicker">图鉴</div><h1>过关的留下，没过关的是空台</h1>
      <div class="stats"><div>过关 ${s.known}</div><div>抓住 ${s.caught}</div><div class="trust">可信度 ${Array.from({ length: 5 }, (_, i) => `<i class="${i < s.trust ? "on" : ""}"></i>`).join("")}</div></div>
      ${(s.diary || []).map((line) => `<div class="sentence">${esc(line)}</div>`).join("") || `<div class="sentence fogged">这里会放今天过关的句子</div>`}
      <div class="blank">空白台座</div></section>`;
  },
  async "/app/chat"() {
    const me = (await api("/api/me")).user;
    const listed = await api("/api/chat/sessions");
    let sessions = listed.sessions;
    let current = sessions[0] ? sessions[0].id : 0;
    document.body.classList.add("harness");
    const model = me.api_model || "未连接模型";
    const keyHint = me.has_key ? "Key ····" + (me.key_last4 || "") : "未填写 Key";
    const shell = () => {
      room.innerHTML = `
        <div class="dsh">
          <aside class="dsh-side">
            <div class="dsh-menu"><a href="/app/home">应用</a><a href="/app/settings">编辑</a></div>
            <div class="dsh-brand"><i></i>课笺<small>HARNESS</small></div>
            <button class="dsh-new" id="new-chat" type="button">＋ 新会话</button>
            <button class="dsh-link" id="open-keys" type="button">插件</button>
            <a class="dsh-link" href="/app/plan">自动化任务</a>
            <div class="dsh-label"><span>工作区</span><span id="chat-count"></span></div>
            <div class="dsh-list" id="chat-list">${sessions.map((s) => `<button class="dsh-item${s.id === current ? " on" : ""}" data-id="${s.id}" type="button">${esc(s.title)}</button>`).join("") || `<p class="lbl">还没有会话</p>`}</div>
          </aside>
          <section class="dsh-main">
            <div class="dsh-top"><a href="/">课笺 / 助手</a><span>${esc(model)} · ${keyHint}</span></div>
            <div id="log" class="dsh-log"></div>
            <form id="api-form" class="dsh-keys">
              <input name="api_base" placeholder="接口地址，以 /v1 结尾" value="${esc(me.api_base || "")}">
              <input name="api_model" placeholder="模型名" value="${esc(me.api_model || "")}">
              <input name="api_key" placeholder="${me.has_key ? "留空则不改 Key" : "API Key"}" type="password">
              <button class="dsh-new" type="submit">保存</button>
            </form>
            <form id="composer" class="dsh-composer">
              <input name="text" type="text" placeholder="发消息或创建任务，/ 调用指令" autocomplete="off">
              <div class="dsh-bar"><span>确认后写入</span><span>${esc(model)} <button class="dsh-send" type="submit">↑</button></span></div>
            </form>
          </section>
        </div>`;
      room.querySelector("#new-chat").onclick = async () => {
        const body = await api("/api/chat/sessions", { method: "POST" });
        sessions = [{ id: body.id, title: "新的对话" }, ...sessions];
        current = body.id;
        shell();
        await load();
      };
      room.querySelector("#open-keys").onclick = () => room.querySelector("#api-form").classList.toggle("open");
      room.querySelectorAll(".dsh-item").forEach((btn) => btn.onclick = async () => {
        current = Number(btn.dataset.id);
        shell();
        await load();
      });
      room.querySelector("#api-form").onsubmit = async (e) => {
        e.preventDefault();
        const fd = new FormData(e.target);
        const payload = { api_base: fd.get("api_base"), api_model: fd.get("api_model") };
        if (fd.get("api_key")) payload.api_key = fd.get("api_key");
        await api("/api/settings", { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        location.reload();
      };
      room.querySelector("#composer").onsubmit = async (e) => {
        e.preventDefault();
        const text = new FormData(e.target).get("text");
        if (!String(text || "").trim()) return;
        if (!current) {
          const body = await api("/api/chat/sessions", { method: "POST" });
          current = body.id;
        }
        e.target.reset();
        await stream(`/api/chat/sessions/${current}/turns`, { text });
      };
    };
    const load = async () => {
      if (!current) {
        room.querySelector("#log").innerHTML = `<p class="lbl">还没有对话。保存模型后，从下面发送第一句。</p>`;
        room.querySelector("#chat-count").textContent = "0 条事件";
        return;
      }
      const data = await api("/api/chat/sessions/" + current);
      room.querySelector("#chat-count").textContent = data.count + " 条事件";
      const done = new Set();
      for (const ev of data.events) {
        if (ev.type === "tool_result") done.add(JSON.parse(ev.payload).call_id);
      }
      room.querySelector("#log").innerHTML = data.events.map((ev) => renderEvent(ev, done)).join("");
      room.querySelectorAll("[data-tool]").forEach((btn) => btn.onclick = async () => {
        await stream("/api/chat/tools/" + btn.dataset.tool, { accept: btn.dataset.accept === "1" });
      });
      const log = room.querySelector("#log");
      log.scrollTop = log.scrollHeight;
    };
    const stream = async (url, payload) => {
      const res = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        room.querySelector("#log").insertAdjacentHTML("beforeend", `<p class="err">${esc(body.error || "没有发出去")}</p>`);
        return;
      }
      const live = document.createElement("div");
      live.className = "dsh-msg";
      room.querySelector("#log").appendChild(live);
      await readSSE(res, (event, data) => {
        if (event === "chunk" && data.text) live.textContent += data.text;
        if (event === "error") live.textContent = data.error || "模型没有完成";
      });
      const listed = await api("/api/chat/sessions");
      sessions = listed.sessions;
      shell();
      await load();
    };
    shell();
    await load();
  },
};

const render = pages[location.pathname] || pages["/app/home"];
render().then(() => {
  if (!window.anime || document.body.classList.contains("harness")) return;
  anime({
    targets: "#room .room > *, #room .path .node, #room .flip, #room .card",
    translateY: [18, 0],
    opacity: [0, 1],
    delay: anime.stagger(55),
    duration: 520,
    easing: "easeOutCubic",
  });
}).catch((err) => { room.innerHTML = `<section class="room"><p>${esc(err.message)}</p></section>`; });
