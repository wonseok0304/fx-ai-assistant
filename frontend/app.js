"use strict";
const API = (window.API_BASE_URL || "").replace(/\/$/, "");
const $ = (id) => document.getElementById(id);
const PAGE_SIZE = 10;

const state = { conversationId: null, data: [], page: 0, stats: null, sending: false };

/* ---------- 공통 ---------- */
function toast(msg) {
  const t = $("toast");
  t.textContent = msg; t.hidden = false;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => (t.hidden = true), 2500);
}
function showError(msg) {
  const b = $("errorBanner");
  b.textContent = msg; b.hidden = !msg;
}
async function api(path, options = {}) {
  // 콜드스타트 안내: 3초 넘게 걸리면 배너 표시
  const timer = setTimeout(() => ($("wakeBanner").hidden = false), 3000);
  try {
    const res = await fetch(API + path, {
      headers: { "Content-Type": "application/json" }, ...options,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      const d = body.detail;
      const msg = Array.isArray(d) ? d.map((e) => e.msg).join(", ") : d || `요청 실패 (${res.status})`;
      throw new Error(msg);
    }
    showError("");
    return res.json();
  } catch (e) {
    if (e instanceof TypeError) throw new Error("서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요.");
    throw e;
  } finally {
    clearTimeout(timer);
    $("wakeBanner").hidden = true;
  }
}
const fmt = (n) => (n == null ? "-" : Number(n).toLocaleString("ko-KR", { maximumFractionDigits: 2 }));
function el(tag, props = {}, ...kids) {
  const e = Object.assign(document.createElement(tag), props);
  kids.forEach((k) => e.append(k));
  return e;
}

/* ---------- 다크 모드 ---------- */
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  $("themeToggle").textContent = theme === "dark" ? "☀️" : "🌙";
  try { localStorage.setItem("theme", theme); } catch {}
  if (state.data.length) drawChart();
}
$("themeToggle").onclick = () =>
  applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");

/* ---------- 요약 ---------- */
async function loadSummary() {
  const box = $("summary");
  try {
    const s = await api("/api/data/summary");
    if (!s.count) { box.textContent = "저장된 데이터가 없습니다. 아래에서 추가해 주세요."; return; }
    const m = s.metrics;
    const dir = s.trend.startsWith("상승") ? "up" : s.trend.startsWith("하락") ? "down" : "";
    box.replaceChildren(
      stat("기간", s.period), stat("데이터 수", `${s.count}개`),
      stat("최근값", `${fmt(m.latest)}원`), stat("평균", `${fmt(m.average)}원`),
      stat("최고", `${fmt(m.max)}원 (${m.max_date})`), stat("최저", `${fmt(m.min)}원 (${m.min_date})`),
      stat("일간 변동성", `${m.volatility_pct}%`), stat("최근 7건 변화", `${m.change_7d_pct}%`),
      stat("추세", s.trend, "trend " + dir),
    );
  } catch (e) { box.textContent = ""; showError(e.message); }
}
function stat(label, value, cls = "") {
  const b = el("b", { textContent: value });
  if (cls.includes("up")) b.className = "up"; if (cls.includes("down")) b.className = "down";
  return el("div", { className: "stat " + (cls.includes("trend") ? "trend" : "") }, el("small", { textContent: label }), b);
}

/* ---------- 채팅 ---------- */
function addMessage(role, content, meta) {
  const m = $("messages");
  m.querySelector(".empty")?.remove();
  const div = el("div", { className: "msg " + role, textContent: content });
  if (meta) div.append(el("small", { textContent: meta }));
  m.append(div);
  m.scrollTop = m.scrollHeight;
  return div;
}
function resetChat() {
  state.conversationId = null;
  $("messages").replaceChildren(el("div", { className: "empty", textContent: "환율 데이터에 대해 무엇이든 물어보세요." }));
  renderConversations();
}
$("newChat").onclick = resetChat;

$("chatForm").onsubmit = async (ev) => {
  ev.preventDefault();
  if (state.sending) return;
  const text = $("chatInput").value.trim();
  if (!text) return;
  state.sending = true; $("sendBtn").disabled = true; $("chatInput").value = "";
  addMessage("user", text);
  const loading = addMessage("assistant", "");
  loading.classList.add("typing");
  loading.append(el("span"), el("span"), el("span"));
  try {
    const r = await api("/api/chat", {
      method: "POST", body: JSON.stringify({ message: text, conversation_id: state.conversationId }),
    });
    loading.remove();
    const tools = r.tools_used.length ? "🔧 " + r.tools_used.map((t) => t.name).join(", ") : "";
    addMessage("assistant", r.reply, tools);
    if (r.conversation_id) state.conversationId = r.conversation_id;
    if (!r.saved) toast("⚠️ 답변은 생성됐지만 대화 저장에 실패했습니다.");
    loadConversations();
  } catch (e) {
    loading.remove();
    addMessage("assistant", "⚠️ " + e.message);
  } finally {
    state.sending = false; $("sendBtn").disabled = false; $("chatInput").focus();
  }
};

/* ---------- 대화 기록 ---------- */
let conversations = [];
async function loadConversations() {
  try { conversations = await api("/api/conversations"); renderConversations(); }
  catch (e) { showError(e.message); }
}
function renderConversations() {
  const ul = $("convList");
  if (!conversations.length) { ul.replaceChildren(el("li", { textContent: "저장된 대화가 없습니다." })); return; }
  ul.replaceChildren(...conversations.map((c) => {
    const del = el("button", { className: "ghost danger", textContent: "삭제", title: "대화 삭제" });
    del.onclick = async (ev) => {
      ev.stopPropagation();
      if (!confirm("이 대화를 삭제할까요?")) return;
      try {
        await api(`/api/conversations/${c.id}`, { method: "DELETE" });
        if (state.conversationId === c.id) resetChat();
        toast("대화를 삭제했습니다."); loadConversations();
      } catch (e) { showError(e.message); }
    };
    const li = el("li", { className: c.id === state.conversationId ? "active" : "" },
      el("div", { className: "t" }, c.title || "(제목 없음)",
        el("small", { textContent: `${c.message_count}개 메시지 · ${new Date(c.updated_at).toLocaleString("ko-KR")}` })),
      del);
    li.onclick = () => openConversation(c.id);
    return li;
  }));
}
async function openConversation(id) {
  try {
    const c = await api(`/api/conversations/${id}`);
    state.conversationId = c.id;
    $("messages").replaceChildren();
    c.messages.forEach((m) => addMessage(m.role, m.content));
    renderConversations();
  } catch (e) { showError(e.message); }
}

/* ---------- 데이터 관리 ---------- */
async function loadData() {
  try {
    state.data = await api("/api/data");
    renderTable(); drawChart();
  } catch (e) { showError(e.message); }
}
function renderTable() {
  const rows = [...state.data].reverse();  // 최신순
  const pages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  state.page = Math.min(state.page, pages - 1);
  const slice = rows.slice(state.page * PAGE_SIZE, (state.page + 1) * PAGE_SIZE);
  $("dataBody").replaceChildren(...slice.map((r) => {
    const edit = el("button", { className: "ghost", textContent: "수정" });
    edit.onclick = () => startEdit(r);
    const del = el("button", { className: "ghost danger", textContent: "삭제" });
    del.onclick = async () => {
      if (!confirm(`${r.date} 데이터를 삭제할까요?`)) return;
      try { await api(`/api/data/${r.id}`, { method: "DELETE" }); toast("삭제했습니다."); refreshAll(); }
      catch (e) { showError(e.message); }
    };
    return el("tr", {},
      el("td", { textContent: r.date }), el("td", { textContent: fmt(r.value) }),
      el("td", { className: "memo", textContent: r.memo || "" }),
      el("td", { className: "act" }, edit, " ", del));
  }));
  $("pageInfo").textContent = `${state.page + 1} / ${pages} (총 ${rows.length}건)`;
  $("prevPage").disabled = state.page === 0;
  $("nextPage").disabled = state.page >= pages - 1;
}
$("prevPage").onclick = () => { state.page--; renderTable(); };
$("nextPage").onclick = () => { state.page++; renderTable(); };

function startEdit(r) {
  $("dataId").value = r.id; $("dDate").value = r.date; $("dValue").value = r.value; $("dMemo").value = r.memo || "";
  $("dSubmit").textContent = "수정 저장"; $("dCancel").hidden = false;
  $("dataForm").scrollIntoView({ behavior: "smooth", block: "center" });
}
function resetForm() {
  $("dataForm").reset(); $("dataId").value = "";
  $("dSubmit").textContent = "추가"; $("dCancel").hidden = true;
}
$("dCancel").onclick = resetForm;
$("dataForm").onsubmit = async (ev) => {
  ev.preventDefault();
  const id = $("dataId").value;
  const body = JSON.stringify({ date: $("dDate").value, value: parseFloat($("dValue").value), memo: $("dMemo").value });
  try {
    await api(id ? `/api/data/${id}` : "/api/data", { method: id ? "PUT" : "POST", body });
    toast(id ? "수정되었습니다." : "추가되었습니다.");
    resetForm(); refreshAll();
  } catch (e) { showError(e.message); }
};

// 내보내기
$("exportCsv").href = API + "/api/data/export?format=csv";
$("exportJson").href = API + "/api/data/export?format=json";

/* ---------- 그래프 (Canvas) ---------- */
async function drawChart() {
  const canvas = $("chart");
  const data = state.data;
  const ctx = canvas.getContext("2d");
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = 260;
  canvas.width = w * dpr; canvas.height = h * dpr; ctx.scale(dpr, dpr);
  ctx.clearRect(0, 0, w, h);
  if (data.length < 2) return;

  const css = getComputedStyle(document.documentElement);
  const color = (v) => css.getPropertyValue(v).trim();
  const vals = data.map((d) => d.value);
  const ma = vals.map((_, i) => { const s = vals.slice(Math.max(0, i - 6), i + 1); return s.reduce((a, b) => a + b) / s.length; });
  const min = Math.min(...vals), max = Math.max(...vals), pad = (max - min) * 0.1 || 1;
  const L = 52, R = 12, T = 12, B = 26;
  const x = (i) => L + (i / (data.length - 1)) * (w - L - R);
  const y = (v) => T + (1 - (v - (min - pad)) / (max - min + 2 * pad)) * (h - T - B);

  ctx.font = "11px system-ui"; ctx.fillStyle = color("--muted"); ctx.strokeStyle = color("--border");
  for (let i = 0; i <= 4; i++) {
    const v = min - pad + ((max - min + 2 * pad) * i) / 4;
    ctx.beginPath(); ctx.moveTo(L, y(v)); ctx.lineTo(w - R, y(v)); ctx.stroke();
    ctx.fillText(Math.round(v).toLocaleString(), 4, y(v) + 4);
  }
  [0, Math.floor(data.length / 2), data.length - 1].forEach((i) => {
    ctx.textAlign = i === 0 ? "left" : i === data.length - 1 ? "right" : "center";
    ctx.fillText(data[i].date, x(i), h - 8);
  });
  const line = (arr, c, lw) => {
    ctx.beginPath(); ctx.strokeStyle = c; ctx.lineWidth = lw;
    arr.forEach((v, i) => (i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v)))); ctx.stroke();
  };
  line(vals, color("--line"), 1.5); line(ma, color("--ma"), 2);

  canvas.onmousemove = (ev) => {
    const rect = canvas.getBoundingClientRect();
    const i = Math.round(((ev.clientX - rect.left - L) / (w - L - R)) * (data.length - 1));
    const tip = $("chartTip");
    if (i < 0 || i >= data.length) { tip.hidden = true; return; }
    tip.hidden = false;
    tip.textContent = `${data[i].date} · ${fmt(data[i].value)}원`;
    tip.style.left = Math.min(x(i), w - 140) + 16 + "px";
    tip.style.top = y(data[i].value) + canvas.offsetTop - 30 + "px";
  };
  canvas.onmouseleave = () => ($("chartTip").hidden = true);
}
window.addEventListener("resize", () => state.data.length && drawChart());

/* ---------- 초기화 ---------- */
function refreshAll() { loadSummary(); loadData(); }
(function init() {
  let theme = "light";
  try { theme = localStorage.getItem("theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch {}
  applyTheme(theme);
  resetChat();
  refreshAll(); loadConversations();
})();
