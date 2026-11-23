const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const S = { d: null, di: 0, digestMonth: null, digestQuery: "", pickDate: null, pickMonth: null, pickMode: "month", selectedPick: null, selectedSection: null, selectedItem: null };
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const safeUrl = value => { try { const u = new URL(value); return ["http:", "https:"].includes(u.protocol) ? u.href : ""; } catch { return ""; } };
const badge = v => { const s = String(v || "unknown").toLowerCase().replace(/[^a-z0-9_-]/g, "_"), tone = ["success", "done", "completed"].includes(s) ? "success" : ["failed", "error", "skipped", "lapsed"].includes(s) ? "fail" : ["proposed", "in_progress", "running", "pending"].includes(s) ? "warn" : ""; return `<span class="badge ${tone}">${esc(String(v || "unknown").replaceAll("_", " "))}</span>`; };
const empty = (title, text) => `<div class="empty-state"><strong>${esc(title)}</strong>${esc(text)}</div>`;
const head = (title, text) => `<header class="page-heading"><h1>${esc(title)}</h1><p>${esc(text)}</p></header>`;
const section = (title, note = "") => `<div class="section-heading"><h2>${esc(title)}</h2>${note ? `<p>${esc(note)}</p>` : ""}</div>`;
const localDate = value => { const m = String(value || "").match(/^(\d{4})-(\d{2})-(\d{2})/); return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null; };
const date = value => { const d = localDate(value); return d ? d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "Date not recorded"; };
const longDate = value => { const d = localDate(value); return d ? d.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" }) : "Date not recorded"; };
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const monthLabel = d => d.toLocaleDateString(undefined, { month: "long", year: "numeric" });
const shiftMonth = (d, amount) => new Date(d.getFullYear(), d.getMonth() + amount, 1);
const startWeek = d => { const x = new Date(d); x.setDate(x.getDate() - ((x.getDay() + 6) % 7)); x.setHours(0, 0, 0, 0); return x; };
const digestDate = d => d.date || (d.file || "").match(/pulse_digest_(\d{4})(\d{2})(\d{2})/)?.slice(1).join("-");

function inline(text) {
  let out = "", pos = 0;
  const re = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)|(https?:\/\/[^\s<>\]]+)/g;
  for (const m of text.matchAll(re)) {
    out += esc(text.slice(pos, m.index));
    const url = safeUrl(m[2] || m[3]);
    if (!url) out += esc(m[0]);
    else out += `<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(m[1] || m[3])}</a>`;
    pos = m.index + m[0].length;
  }
  out += esc(text.slice(pos));
  return out.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>");
}
function md(source) {
  const out = []; let list = false;
  for (const line of (source || "").split(/\r?\n/)) {
    const h = line.match(/^(#{1,3})\s+(.+)$/), li = line.match(/^\s*[-*]\s+(.+)$/);
    if (h) { if (list) { out.push("</ul>"); list = false; } const label = h[2], idLabel = label.replace(/\s+\(\d+ items?\)$/, ""), id = `digest-${idLabel.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}`; out.push(`<h${h[1].length} id="${esc(id)}">${inline(label)}</h${h[1].length}>`); }
    else if (li) { if (!list) { out.push("<ul>"); list = true; } out.push(`<li>${inline(li[1])}</li>`); }
    else { if (list) { out.push("</ul>"); list = false; } if (/^---+$/.test(line.trim())) out.push("<hr>"); else if (line.trim()) out.push(`<p>${inline(line)}</p>`); }
  }
  if (list) out.push("</ul>");
  return out.join("");
}
function runs(items, kind) {
  return items.length ? items.slice(0, 5).map(x => `<div class="data-row"><div><div class="row-title">${esc(x.run_key)}</div><div class="row-meta">${esc(kind === "p" ? `${x.error_count || 0} source issues` : x.action || x.error || "Weekly activity")}</div></div>${badge(x.status)}</div>`).join("") : empty("No runs yet", "Records appear after a workflow runs.");
}
function overview(d) {
  const p = d.pulse_runs[0], v = d.pulsedev_runs[0], evidence = d.profile?.evidence || [], done = d.picks.filter(x => x.status === "done").length, open = d.picks.filter(x => ["proposed", "in_progress"].includes(x.status)).length;
  return `<div class="overview-lead"><div class="lead-main"><h1>Pulse at a glance</h1><p>Your digest archive, weekly development work, and learning profile in one local view.</p></div><div class="lead-side"><div class="lead-label">Most recent activity</div><div>Pulse ${p ? badge(p.status) : "has no run record"}</div><div class="lead-meta">${esc(p?.run_key || "No recent run")}</div><div>PulseDev ${v ? badge(v.status) : "has no run record"}</div><div class="lead-meta">${esc(v?.run_key || "No weekly run")}</div></div></div><div class="metric-strip">${[["Saved digests", d.digests.length, "Daily archive"], ["Learning picks", d.picks.length, `${done} completed, ${open} open`], ["Profile evidence", evidence.length, "Linked proofs"], ["Tracked topics", d.topics.length, "Configured in Pulse"]].map(x => `<div class="metric"><div class="metric-label">${x[0]}</div><div class="metric-value">${x[1]}</div><div class="metric-note">${x[2]}</div></div>`).join("")}</div><div class="layout-main-side"><section>${section("Recent activity", "Workflow records saved here")}<div class="layout-two"><article class="surface"><h2>Pulse runs</h2>${runs(d.pulse_runs, "p")}</article><article class="surface"><h2>PulseDev runs</h2>${runs(d.pulsedev_runs, "d")}</article></div>${section("Learning evidence", "Completed work connected to your profile")}<article class="surface">${evidence.length ? evidence.slice(-4).reverse().map(x => `<div class="data-row"><div>${esc(x.title)}<div class="row-meta">${esc(x.proof_path)}</div></div>${badge(x.rating ? `${x.rating}/5` : "Covered")}</div>`).join("") : empty("No linked evidence yet", "Completed work can be linked through the learning log.")}</article></section><aside>${section("Pulse configuration")}<article class="surface"><h2>Tracked topics</h2><div class="chip-list">${d.topics.map(x => `<span class="chip">${esc(x.name)} · Priority ${esc(x.priority)}</span>`).join("")}</div><h3>Source tracking</h3><p class="row-meta">Documentation: ${esc(d.hash_counts["docs_hashes.json"] || 0)}</p><p class="row-meta">GitHub READMEs: ${esc(d.hash_counts["github_readme_hashes.json"] || 0)}</p></article><article class="surface"><h2>Configured models</h2>${["base", "summarization", "picker"].map(x => `<div class="data-row">${x}<span class="row-meta">${esc(d.models[x] || "Not configured")}</span></div>`).join("")}</article></aside></div>`;
}

function profile(d) {
  const p = d.profile;
  if (!d.learning_log_path) return head("User profile", "A map of topics and the learning proof linked to them.") + `<article class="surface">${empty("Connect your learning log", "Set LEARNING_LOG_PATH in .env to a local clone, then restart the dashboard.")}</article>`;
  if (p?.error) return head("User profile", "Knowledge topics and linked proof.") + `<article class="notice notice-error"><h2>Profile could not be read</h2><p>${esc(p.error)}</p></article>`;
  if (!p) return head("User profile", "A map of topics and the learning proof linked to them.") + `<article class="surface">${empty("No profile found", "Create a profile in the connected learning log, then reload.")}<p><code>uv run python -m src.pulsedev.cli profile-init --learning-log "${esc(d.learning_log_path)}"</code></p></article>`;
  const sections = p.sections || [], evidence = p.evidence || [];
  if (!S.selectedSection || !sections.some(x => x.id === S.selectedSection)) S.selectedSection = sections[0]?.id || null;
  const sectionData = sections.find(x => x.id === S.selectedSection), items = (sectionData?.items || []).filter(x => !x.merged_into);
  if (!items.some(x => x.id === S.selectedItem)) S.selectedItem = items[0]?.id || null;
  const selected = items.find(x => x.id === S.selectedItem), sources = (selected?.evidence_ids || []).map(id => evidence.find(x => x.pick_id === id)).filter(Boolean);
  const graphHeight = Math.max(360, items.length * 88 + 44), rootY = graphHeight / 2;
  const nodes = items.map((item, i) => ({ item, y: 44 + i * 88 }));
  const graph = sectionData ? `<svg class="knowledge-map" viewBox="0 0 760 ${graphHeight}" role="group" aria-label="${esc(sectionData.name)} topic map">${nodes.map(n => `<line class="graph-edge" x1="180" y1="${rootY}" x2="475" y2="${n.y + 25}"/>`).join("")}<g class="graph-root"><circle cx="105" cy="${rootY}" r="56"/><text x="105" y="${rootY - 3}" text-anchor="middle">${esc(sectionData.name.length > 15 ? sectionData.name.slice(0, 13) + "…" : sectionData.name)}</text><text class="graph-count" x="105" y="${rootY + 17}" text-anchor="middle">${items.length} topics</text></g>${nodes.map(({ item, y }) => `<g class="graph-node ${item.id === S.selectedItem ? "is-selected" : ""}" data-item="${esc(item.id)}" role="button" tabindex="0" aria-label="Explore ${esc(item.name)}"><rect x="420" y="${y}" width="292" height="50" rx="10"/><circle cx="445" cy="${y + 25}" r="5"/><text x="462" y="${y + 30}">${esc(item.name.length > 32 ? item.name.slice(0, 30) + "…" : item.name)}</text></g>`).join("")}</svg>` : empty("Your map is ready for topics", "Add sections and topic labels in profile.json to explore your knowledge graph.");
  const detail = selected ? `<div class="map-detail"><p class="eyebrow">${esc(sectionData.name)}</p><h3>${esc(selected.name)}</h3><div class="date-pair"><span>First linked ${date(selected.first_seen)}</span><span>Most recent ${date(selected.last_seen)}</span></div><h4>Linked learning proof <span class="count-pill">${sources.length}</span></h4>${sources.length ? sources.map(x => `<button class="proof-row" data-proof="${esc(x.pick_id)}"><span>${esc(x.title)}</span><small>${date(x.completed_at)} · Open pick</small></button>`).join("") : `<p class="subtle">No completed pick is linked to this topic yet.</p>`}</div>` : `<div class="map-detail">${empty("Choose a topic", "Select a node to see its linked learning proof and dates.")}</div>`;
  return head("Learning profile", "Explore topic clusters and follow each one back to completed learning proof.") + `<article class="surface profile-intro"><div><p class="eyebrow">LONG-TERM DIRECTION</p><h2>${esc(p.summary || "Your learning profile")}</h2><p>${esc(p.knowledge_notes || "Your profile groups learning topics and connects them to completed picks.")}</p></div><div class="profile-total"><strong>${sections.length}</strong><span>sections</span><strong>${sections.reduce((n, x) => n + x.items.filter(i => !i.merged_into).length, 0)}</strong><span>topics</span></div></article><div class="profile-explorer"><section class="surface explorer-map">${section("Knowledge graph", sectionData ? `${items.length} topics · select a node to inspect proof` : "Select a section to explore")}<div class="section-pills">${sections.map(x => `<button class="section-pill ${x.id === S.selectedSection ? "active" : ""}" data-section="${esc(x.id)}">${esc(x.name)} <span>${x.items.filter(i => !i.merged_into).length}</span></button>`).join("")}</div><div class="graph-scroll">${graph}</div></section><aside class="surface explorer-detail"><p class="eyebrow">TOPIC DETAILS</p>${detail}</aside></div><article class="surface evidence-shelf">${section("All completed proof", `${evidence.length} linked picks`)}${evidence.length ? `<div class="evidence-strip">${evidence.slice().reverse().map(x => `<button class="proof-row" data-proof="${esc(x.pick_id)}"><span>${esc(x.title)}</span><small>${date(x.completed_at)} · ${esc(x.proof_path)}</small></button>`).join("")}</div>` : empty("No completed picks linked", "Complete a pick to add its proof to your profile.")}</article>`;
}

function digestCalendar() {
  const month = S.digestMonth, year = month.getFullYear(), m = month.getMonth(), offset = (new Date(year, m, 1).getDay() + 6) % 7, count = new Date(year, m + 1, 0).getDate();
  const byDay = new Map(); S.d.digests.forEach((d, i) => { const key = digestDate(d); if (key) { const a = byDay.get(key) || []; a.push(i); byDay.set(key, a); } });
  const cells = Array.from({ length: Math.ceil((offset + count) / 7) * 7 }, (_, i) => { const day = i - offset + 1; if (day < 1 || day > count) return `<span class="calendar-blank" aria-hidden="true"></span>`; const key = iso(new Date(year, m, day)), indexes = byDay.get(key) || [], active = indexes.includes(S.di); return `<button class="calendar-day ${indexes.length ? "has-entry" : ""} ${active ? "selected" : ""}" data-digest-day="${key}" ${indexes.length ? `aria-label="${longDate(key)}, ${indexes.length} digest${indexes.length === 1 ? "" : "s"}"` : `aria-label="${longDate(key)}, no digest"`} ${indexes.length ? "" : "disabled"}><span>${day}</span>${indexes.length ? `<i>${indexes.length > 1 ? indexes.length : ""}</i>` : ""}</button>`; }).join("");
  return `<div class="calendar-top"><button class="icon-button" data-digest-month="-1" aria-label="Previous month">‹</button><h2>${esc(monthLabel(month))}</h2><button class="icon-button" data-digest-month="1" aria-label="Next month">›</button></div><div class="calendar-grid calendar-weekdays">${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(x => `<span>${x}</span>`).join("")}</div><div class="calendar-grid">${cells}</div>`;
}
function digestSearchResults() {
  const q = S.digestQuery.trim().toLowerCase(); if (!q) return "";
  const matches = S.d.digests.map((d, i) => ({ d, i })).filter(x => `${digestDate(x.d)} ${x.d.content}`.toLowerCase().includes(q));
  return `<div class="search-results-label">${matches.length} matching digest${matches.length === 1 ? "" : "s"}</div>${matches.length ? matches.slice(0, 12).map(x => `<button class="search-result" data-digest="${x.i}">${esc(longDate(digestDate(x.d)))}<small>${esc(x.d.sources?.length || 0)} source links</small></button>`).join("") : empty("No matching digests", "Try another date or phrase.")}`;
}
function digestBody() {
  const d = S.d.digests[S.di]; if (!d) return empty("No saved digest on this day", "Choose a marked day or move to another month.");
  const content = (d.content || "").replace(/^#\s+⚡?\s*Pulse Daily Digest[^\n]*\n?/, "").replace(/\n---\n\nRun health:[\s\S]*$/i, "");
  const sectionNames = [...content.matchAll(/^##\s+(.+?)\s*$/gm)].map(x => x[1].replace(/\s+\(\d+ items?\)$/, ""));
  const sources = (d.sources || []).filter(s => safeUrl(s.url));
  const toc = sectionNames.length ? `<nav class="digest-toc" aria-label="Digest sections">${sectionNames.map(n => `<a href="#digest-${n.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")}">${esc(n)}</a>`).join("")}</nav>` : "";
  const sourcePanel = sources.length ? `<details class="source-drawer"><summary>Source links <span class="count-pill">${sources.length}</span></summary><div class="source-link-list">${sources.map(source => `<a href="${esc(safeUrl(source.url))}" target="_blank" rel="noopener noreferrer"><span>${esc(source.title || source.url)}</span><small>${esc([source.source_name, source.source_type, source.published_at && date(source.published_at)].filter(Boolean).join(" · ") || new URL(source.url).hostname)} ↗</small></a>`).join("")}</div></details>` : `<p class="no-sources">No source URLs were saved in this digest.</p>`;
  return `<header class="digest-reader-head"><div><p class="eyebrow">PULSE DAILY DIGEST</p><h2>${esc(longDate(digestDate(d)))}</h2><p class="row-meta">Sent ${esc(date(digestDate(d)))} · ${sources.length} source links</p></div><div class="reader-actions"><button class="quiet-button" data-reader="prev" aria-label="Previous digest">← Older</button><button class="quiet-button" data-reader="next" aria-label="Next digest">Newer →</button><button class="quiet-button" data-copy-digest>Copy</button></div></header>${toc}<div class="prose digest-prose">${md(content)}</div>${sourcePanel}`;
}
function digests(d) {
  if (!S.digestMonth) { const latest = localDate(d.digests[0] && digestDate(d.digests[0])); S.digestMonth = latest ? new Date(latest.getFullYear(), latest.getMonth(), 1) : new Date(new Date().getFullYear(), new Date().getMonth(), 1); }
  return head("Digest archive", "Browse each day on a calendar, then read, search, and follow the sources behind the summary.") + `<div class="digest-workspace"><aside class="surface digest-calendar-panel"><div class="archive-count"><span>Saved daily digests</span><strong>${d.digests.length}</strong></div><div class="calendar-controls"><button class="quiet-button" data-latest-digest>Latest digest</button><label class="search-wrap"><span class="sr-only">Search digest dates and content</span><input class="search-input" id="digest-search" type="search" value="${esc(S.digestQuery)}" placeholder="Search dates or topics"></label></div><div id="digest-calendar">${digestCalendar()}</div><div class="calendar-legend"><span><i></i>Digest saved</span><span>Click a marked day to open</span></div><div class="digest-search-results" id="digest-search-results">${digestSearchResults()}</div></aside><article class="surface digest-reader" id="digest-reader">${digestBody()}</article></div>`;
}

function weekLabel(value) { const start = startWeek(value), end = new Date(start); end.setDate(end.getDate() + 6); return `${start.toLocaleDateString(undefined, { month: "short", day: "numeric" })} – ${end.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}`; }
function pickCalendar() {
  const month = S.pickMonth, year = month.getFullYear(), m = month.getMonth(), count = new Date(year, m + 1, 0).getDate(), offset = (new Date(year, m, 1).getDay() + 6) % 7;
  const byDay = new Map(); S.d.picks.forEach((p, i) => { const key = String(p.proposed_at || "").slice(0, 10); if (key) { const list = byDay.get(key) || []; list.push({ p, i }); byDay.set(key, list); } });
  const button = day => { const key = iso(new Date(year, m, day)), found = byDay.get(key) || [], state = found.some(x => x.p.status === "done") ? "done" : found.some(x => ["proposed", "in_progress"].includes(x.p.status)) ? "open" : "other"; return `<button class="calendar-day ${found.length ? `has-entry pick-${state}` : ""} ${key === S.pickDate ? "selected" : ""}" data-pick-day="${key}" aria-label="${longDate(key)}, ${found.length ? `${found.length} pick${found.length === 1 ? "" : "s"}` : "no picks"}"><span>${day}</span>${found.length ? `<i>${found.length > 1 ? found.length : ""}</i>` : ""}</button>`; };
  if (S.pickMode === "week") { const start = startWeek(localDate(S.pickDate) || new Date()), days = Array.from({ length: 7 }, (_, i) => { const x = new Date(start); x.setDate(x.getDate() + i); return x; }); return `<div class="calendar-top"><button class="icon-button" data-pick-week="-1" aria-label="Previous week">‹</button><h2>${esc(weekLabel(start))}</h2><button class="icon-button" data-pick-week="1" aria-label="Next week">›</button></div><div class="week-strip">${days.map(x => { const key = iso(x), entries = byDay.get(key) || []; return `<button class="week-day ${key === S.pickDate ? "selected" : ""} ${entries.length ? "has-entry" : ""}" data-pick-day="${key}"><small>${x.toLocaleDateString(undefined, { weekday: "short" })}</small><strong>${x.getDate()}</strong>${entries.length ? `<i>${entries.length} pick${entries.length === 1 ? "" : "s"}</i>` : "<i>No pick</i>"}</button>`; }).join("")}</div>`; }
  const cells = Array.from({ length: Math.ceil((offset + count) / 7) * 7 }, (_, i) => { const day = i - offset + 1; return day < 1 || day > count ? `<span class="calendar-blank"></span>` : button(day); }).join("");
  return `<div class="calendar-top"><button class="icon-button" data-pick-month="-1" aria-label="Previous month">‹</button><h2>${esc(monthLabel(month))}</h2><button class="icon-button" data-pick-month="1" aria-label="Next month">›</button></div><div class="calendar-grid calendar-weekdays">${["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map(x => `<span>${x}</span>`).join("")}</div><div class="calendar-grid">${cells}</div>`;
}
function pickDayContent() {
  const key = S.pickDate, found = S.d.picks.map((p, i) => ({ p, i })).filter(x => String(x.p.proposed_at || "").slice(0, 10) === key);
  if (!found.length) return `<div class="selected-day-heading"><p class="eyebrow">SELECTED DATE</p><h3>${esc(longDate(key))}</h3></div>${empty("No pick on this day", "PulseDev creates one weekly pick. Marked days show when a pick was proposed.")}`;
  return `<div class="selected-day-heading"><p class="eyebrow">WEEKLY WORK · ${found.length} PICK${found.length === 1 ? "" : "S"}</p><h3>${esc(longDate(key))}</h3></div>${found.map(({ p, i }) => `<button class="pick-event ${i === S.selectedPick ? "active" : ""}" data-pick="${i}"><span class="pick-event-date">${badge(p.status)}</span><strong>${esc(p.title)}</strong><small>${esc(p.first_step || "Open pick details")}</small></button>`).join("")}`;
}
function pickDetail() { const p = S.d.picks[S.selectedPick]; return p ? `<div class="pick-detail-top"><div><p class="eyebrow">PICK DETAILS</p><h3>${esc(p.title)}</h3></div>${badge(p.status)}</div><p class="row-meta">Proposed ${esc(date(p.proposed_at))} · ${esc(p.proof_path)}</p><div class="prose">${md(p.body)}</div>` : empty("Choose a pick", "Select a marked calendar day, then open its learning plan."); }
function learning(d) {
  if (!S.pickDate) { const first = d.picks[0] && localDate(d.picks[0].proposed_at); S.pickDate = first ? iso(first) : iso(new Date()); }
  if (!S.pickMonth) { const x = localDate(S.pickDate); S.pickMonth = new Date((x || new Date()).getFullYear(), (x || new Date()).getMonth(), 1); }
  const views = `<div class="view-switch" role="group" aria-label="Calendar view"><button class="${S.pickMode === "month" ? "active" : ""}" data-pick-mode="month">Month</button><button class="${S.pickMode === "week" ? "active" : ""}" data-pick-mode="week">Week</button></div>`;
  return head("PulseDev calendar", "See the weekly learning rhythm, find a past pick, and open its work from the calendar.") + `<div class="dev-calendar-layout"><section class="surface dev-calendar-panel"><div class="calendar-panel-head"><div><p class="eyebrow">LEARNING SCHEDULE</p><h2>Learning rhythm</h2></div>${views}</div><div id="pick-calendar">${pickCalendar()}</div><div class="calendar-legend"><span><i class="legend-open"></i>Proposed or in progress</span><span><i class="legend-done"></i>Completed</span></div><div class="pick-day-list" id="pick-day-list">${pickDayContent()}</div></section><aside class="surface dev-detail" id="pick-detail">${pickDetail()}</aside><section class="surface dev-run-history"><div class="section-heading"><h2>Picker decisions</h2><p>Recent weekly alternatives</p></div>${d.pulsedev_runs.filter(x => x.candidates?.length).slice(0, 6).map(r => `<details class="run-record"><summary><span>${esc(r.run_key)}</span>${badge(r.status)}<small>${esc(r.selection_reason || "Weekly selection")}</small></summary><div class="run-candidates">${(r.candidates || []).map((c, i) => `<div class="candidate ${i === r.selected_index ? "selected" : ""}"><h3>${i === r.selected_index ? "Selected · " : ""}${esc(c.title)}</h3><p>${esc(c.rationale)}</p></div>`).join("")}</div></details>`).join("") || empty("No picker history", "Candidate decisions appear after a weekly run.")}</section></div>`;
}

function activate(name, focus = false) {
  $$(".page").forEach(x => { x.hidden = x.id !== name; x.classList.toggle("active", x.id === name); });
  $$("[data-tab]").forEach(x => { const on = x.dataset.tab === name; x.classList.toggle("active", on); x.setAttribute("aria-selected", on); x.tabIndex = on ? 0 : -1; if (on && focus) x.focus({ preventScroll: true }); });
  $("#current-section").textContent = ({ overview: "Overview", profile: "Learning profile", digests: "Digest archive", learning: "PulseDev calendar" })[name];
}
function renderDigestSelection() { $("#digest-calendar").innerHTML = digestCalendar(); $("#digest-reader").innerHTML = digestBody(); $("#digest-search-results").innerHTML = digestSearchResults(); }
function renderPickSelection() { $("#pick-calendar").innerHTML = pickCalendar(); $("#pick-day-list").innerHTML = pickDayContent(); $("#pick-detail").innerHTML = pickDetail(); }
function renderProfile() { $("#profile").innerHTML = profile(S.d); }
function focusData(attr, key, value) { const node = $$(`[${attr}]`).find(x => x.dataset[key] === String(value)); node?.focus({ preventScroll: true }); }

$(".section-nav").addEventListener("click", e => { const tab = e.target.closest("[data-tab]"); if (tab) activate(tab.dataset.tab); });
$(".mobile-nav").addEventListener("click", e => { const tab = e.target.closest("[data-tab]"); if (tab) activate(tab.dataset.tab); });
document.addEventListener("keydown", e => { const list = e.target.closest('[role="tablist"]'); if (!list) return; const tabs = $$('[role="tab"]', list), i = tabs.indexOf(document.activeElement); const next = e.key === "Home" ? 0 : e.key === "End" ? tabs.length - 1 : ["ArrowRight", "ArrowDown"].includes(e.key) ? (i + 1) % tabs.length : ["ArrowLeft", "ArrowUp"].includes(e.key) ? (i - 1 + tabs.length) % tabs.length : -1; if (i >= 0 && next >= 0) { e.preventDefault(); activate(tabs[next].dataset.tab, true); } });
document.addEventListener("input", e => { if (e.target.id === "digest-search") { S.digestQuery = e.target.value; $("#digest-search-results").innerHTML = digestSearchResults(); } });
document.addEventListener("click", async e => {
  const digest = e.target.closest("[data-digest]"); if (digest) { S.di = +digest.dataset.digest; const d = localDate(digestDate(S.d.digests[S.di])); if (d) S.digestMonth = new Date(d.getFullYear(), d.getMonth(), 1); renderDigestSelection(); focusData("data-digest", "digest", S.di); return; }
  const digestDay = e.target.closest("[data-digest-day]"); if (digestDay) { const key = digestDay.dataset.digestDay, found = S.d.digests.findIndex(x => digestDate(x) === key); if (found >= 0) { S.di = found; renderDigestSelection(); focusData("data-digest-day", "digestDay", key); } return; }
  const digestMonth = e.target.closest("[data-digest-month]"); if (digestMonth) { const direction = digestMonth.dataset.digestMonth; S.digestMonth = shiftMonth(S.digestMonth, +direction); renderDigestSelection(); focusData("data-digest-month", "digestMonth", direction); return; }
  if (e.target.closest("[data-latest-digest]")) { if (S.d.digests.length) { S.di = 0; const d = localDate(digestDate(S.d.digests[0])); S.digestMonth = new Date(d.getFullYear(), d.getMonth(), 1); renderDigestSelection(); focusData("data-latest-digest", "latestDigest", ""); } return; }
  const reader = e.target.closest("[data-reader]"); if (reader) { const which = reader.dataset.reader, step = which === "prev" ? 1 : -1, next = S.di + step; if (next >= 0 && next < S.d.digests.length) { S.di = next; renderDigestSelection(); focusData("data-reader", "reader", which); } return; }
  if (e.target.closest("[data-copy-digest]")) { const d = S.d.digests[S.di]; if (d && navigator.clipboard) { const b = e.target.closest("[data-copy-digest]"); try { await navigator.clipboard.writeText(d.content); b.textContent = "Copied"; setTimeout(() => { if (b.isConnected) b.textContent = "Copy"; }, 1600); } catch { b.textContent = "Copy failed"; } } return; }
  const sourceTab = e.target.closest("[data-section]"); if (sourceTab) { S.selectedSection = sourceTab.dataset.section; S.selectedItem = null; renderProfile(); focusData("data-section", "section", S.selectedSection); return; }
  const node = e.target.closest("[data-item]"); if (node) { S.selectedItem = node.dataset.item; renderProfile(); focusData("data-item", "item", S.selectedItem); return; }
  const proof = e.target.closest("[data-proof]"); if (proof) { S.selectedPick = S.d.picks.findIndex(x => x.id === proof.dataset.proof); if (S.selectedPick >= 0) { S.pickDate = String(S.d.picks[S.selectedPick].proposed_at || "").slice(0, 10) || S.pickDate; const d = localDate(S.pickDate); if (d) S.pickMonth = new Date(d.getFullYear(), d.getMonth(), 1); activate("learning"); renderPickSelection(); } return; }
  const pickDay = e.target.closest("[data-pick-day]"); if (pickDay) { S.pickDate = pickDay.dataset.pickDay; renderPickSelection(); focusData("data-pick-day", "pickDay", S.pickDate); return; }
  const pick = e.target.closest("[data-pick]"); if (pick) { S.selectedPick = +pick.dataset.pick; renderPickSelection(); focusData("data-pick", "pick", S.selectedPick); return; }
  const pickMonth = e.target.closest("[data-pick-month]"); if (pickMonth) { const direction = pickMonth.dataset.pickMonth; S.pickMonth = shiftMonth(S.pickMonth, +direction); renderPickSelection(); focusData("data-pick-month", "pickMonth", direction); return; }
  const pickWeek = e.target.closest("[data-pick-week]"); if (pickWeek) { const direction = pickWeek.dataset.pickWeek, d = localDate(S.pickDate) || new Date(); d.setDate(d.getDate() + +direction * 7); S.pickDate = iso(d); S.pickMonth = new Date(d.getFullYear(), d.getMonth(), 1); renderPickSelection(); focusData("data-pick-week", "pickWeek", direction); return; }
  const mode = e.target.closest("[data-pick-mode]"); if (mode) { S.pickMode = mode.dataset.pickMode; renderPickSelection(); focusData("data-pick-mode", "pickMode", S.pickMode); }
});
document.addEventListener("keydown", e => { const node = e.target.closest("[data-item]"); if (node && ["Enter", " "].includes(e.key)) { e.preventDefault(); S.selectedItem = node.dataset.item; renderProfile(); } });

async function load() {
  try {
    const response = await fetch("/api/dashboard"); if (!response.ok) throw Error(`Dashboard request failed (${response.status})`);
    const d = await response.json(); for (const k of ["pulse_runs", "pulsedev_runs", "digests", "picks", "topics"]) d[k] ||= []; d.models ||= {}; d.hash_counts ||= {}; S.d = d;
    if (d.digests.length) { const x = localDate(digestDate(d.digests[0])); S.digestMonth = new Date(x.getFullYear(), x.getMonth(), 1); }
    $("#loading").classList.add("hidden"); $("#updated").textContent = `Local data loaded ${new Date(d.generated_at).toLocaleTimeString()}`;
    $("#overview").innerHTML = overview(d); $("#profile").innerHTML = profile(d); $("#digests").innerHTML = digests(d); $("#learning").innerHTML = learning(d);
  } catch (error) { $("#loading").classList.add("hidden"); $("#error").innerHTML = `<strong>Could not load Pulse data.</strong><p>${esc(error.message)}. Start the dashboard with <code>uv run python -m src.dashboard</code>.</p>`; $("#error").classList.remove("hidden"); }
}
load();
