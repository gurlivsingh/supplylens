// SupplyLens demo UI. State lives in the URL hash so every view is linkable (#search?v=hotels&q=...&open=ID).
const $ = (s, el = document) => el.querySelector(s);
const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const aed = (n) => "AED " + Number(n).toLocaleString("en-IN");
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return r.json();
};

function route() {
  const [name, qs] = (location.hash.slice(1) || "search").split("?");
  const params = new URLSearchParams(qs || "");
  document.querySelectorAll(".view").forEach((v) => (v.hidden = v.id !== `view-${name}`));
  document.querySelectorAll("[data-route]").forEach((a) => (a.dataset.route === name ? a.setAttribute("aria-current", "page") : a.removeAttribute("aria-current")));
  ({ search: () => runSearch(params), raw: showRaw, review: showReview, evidence: showEvidence }[name] || (() => {}))();
}

// ---------------------------------------------------------------- search
const form = $("#search-form");
function formParams() {
  const f = new FormData(form);
  const p = new URLSearchParams({ v: f.get("vertical"), q: f.get("q") || "", adults: f.get("adults") || 2, sort: f.get("sort") });
  for (const k of ["refundable", "breakfast", "pickup"]) if (f.get(k)) p.set(k, "1");
  return p;
}
form.addEventListener("submit", (e) => { e.preventDefault(); location.hash = "search?" + formParams(); });
form.addEventListener("change", (e) => { if (e.target.name === "vertical") { form.q.value = ""; location.hash = "search?" + formParams(); } });

async function runSearch(p) {
  const v = p.get("v") || "hotels";
  form.vertical.value = v;
  form.q.value = p.get("q") || "";
  form.adults.value = p.get("adults") || 2;
  form.sort.value = p.get("sort") || "recommended";
  for (const k of ["refundable", "breakfast", "pickup"]) form[k].checked = p.get(k) === "1";
  document.body.className = "v-" + v;
  const qs = new URLSearchParams({ vertical: v, q: form.q.value, adults: form.adults.value, sort: form.sort.value });
  for (const k of ["refundable", "breakfast", "pickup"]) if (p.get(k) === "1") qs.set(k, "true");
  let res;
  try { res = await api("/api/search?" + qs); } catch (err) { $("#summary").textContent = "Search failed: " + err.message; return; }
  const c = res.context;
  $("#context").textContent = v === "hotels"
    ? `Query context: check-in ${c.check_in}, ${c.nights} nights, ${form.adults.value} adults, ${c.rooms} room. Prices are stay totals in AED.`
    : `Query context: ${c.date}, ${form.adults.value} adults. Prices are totals in AED.`;
  const active = Object.entries(res.constraints).filter(([k, val]) => val === true).map(([k]) => ({ refundable: "free cancellation", breakfast: "breakfast", pickup: "hotel pickup" }[k]));
  $("#summary").textContent = `${res.results.length} distinct ${v === "hotels" ? (res.results.length === 1 ? "property" : "properties") : (res.results.length === 1 ? "experience" : "experiences")} shown · ${res.raw_listing_count} raw supplier listings consolidated into ${res.entity_count}` + (active.length ? ` · required: ${active.join(", ")}` : "");
  $("#results").innerHTML = res.results.map((e, i) => resultCard(e, i, p)).join("") || `<li class="card">No eligible result for these constraints. Nothing is shown rather than an unsuitable option. Try removing a requirement.</li>`;
  $("#excluded").innerHTML = res.excluded.length ? `<div class="excluded"><h3>Hidden by hard constraints (${res.excluded.length})</h3><ul>${res.excluded.map((x) => `<li><strong>${esc(x.name)}</strong>: ${esc(x.reasons.join("; "))}</li>`).join("")}</ul></div>` : "";
  const open = p.get("open") || (res.results[0] && res.results[0].id);
  if (open) showDetail(v, open, p); else $("#detail").innerHTML = "";
}

function resultCard(e, i, p) {
  const b = e.best_offer;
  const href = "#search?" + new URLSearchParams({ ...Object.fromEntries(p), open: e.id });
  const variants = e.vertical === "hotels" ? `${e.variant_count} room famil${e.variant_count === 1 ? "y" : "ies"}` : `${e.config.duration_h} h · ${e.config.access} access`;
  return `<li class="card${p.get("open") === e.id ? " active" : ""}">
    <div class="card-foot"><span class="rank">#${i + 1} · score ${e.score.toFixed(2)}</span><span class="price">from ${aed(e.from_aed)}</span></div>
    <h3>${esc(e.name)}</h3>
    <div class="meta"><span>${esc(e.area)}</span><span>${e.suppliers.length} supplier${e.suppliers.length > 1 ? "s" : ""}: ${esc(e.suppliers.join(", "))}</span><span>${variants}</span>${e.review_pairs.length ? `<span class="badge warn">possible duplicate under review</span>` : ""}</div>
    <ul class="reasons">${e.reasons.map((r) => `<li>${esc(r)}</li>`).join("")}</ul>
    <div class="card-foot"><a class="link-btn" href="${href}">Compare ${e.offers.length} offer${e.offers.length > 1 ? "s" : ""} and sources →</a></div>
  </li>`;
}

async function showDetail(v, id, p) {
  const qs = new URLSearchParams({ adults: p.get("adults") || 2 });
  for (const k of ["refundable", "breakfast", "pickup"]) if (p.get(k) === "1") qs.set(k, "true");
  // query-implied constraints (e.g. "free cancellation" typed in the box) are applied by the search endpoint; mirror them here
  const ql = (p.get("q") || "").toLowerCase();
  if (/flexible|free cancellation|refundable/.test(ql)) qs.set("refundable", "true");
  if (v === "hotels" && ql.includes("breakfast")) qs.set("breakfast", "true");
  if (v === "experiences" && ql.includes("pickup")) qs.set("pickup", "true");
  let e;
  try { e = await api(`/api/entity/${v}/${encodeURIComponent(id)}?${qs}`); } catch (err) { $("#detail").innerHTML = `<div class="card">Could not load: ${esc(err.message)}</div>`; return; }
  $("#detail").innerHTML = (v === "hotels" ? hotelDetail(e) : experienceDetail(e)) + offersTable(e) + reviewNote(e);
}

function fieldsBlock(e) {
  const f = e.content.fields;
  const row = (k, label) => {
    const x = f[k];
    if (x.value == null) return `<dt>${label}</dt><dd><em>not supplied</em> <span class="src">(left unknown, never invented)</span></dd>`;
    const alt = x.alternatives.length ? `<br><span class="badge ${x.conflict ? "warn" : ""}">${x.conflict ? "conflict flagged for review" : "variants"}: ${esc(x.alternatives.map((a) => `${a.value} (${a.supplier})`).join(", "))}</span>` : "";
    return `<dt>${label}</dt><dd>${esc(x.value)} <span class="src">via ${esc(x.chosen_from)} · seen in ${esc(x.sources.join(", "))}</span>${alt}</dd>`;
  };
  return `<dl class="fields">${row("name", "Name")}${row("address", "Address")}${row("stars", "Stars")}${row("phone", "Phone")}${row("description", "Description")}
    <dt>Amenities</dt><dd>${e.content.amenities.map((a) => `${esc(a.name)} <span class="src">(${esc(a.sources.join(", "))})</span>`).join(" · ")}</dd></dl>`;
}

function hotelDetail(e) {
  const imgs = e.content.images.map((i) => `<div class="tile"><strong>${esc(i.caption)}</strong><span>Synthetic placeholder<br>${esc(i.hash)}<br>source: ${esc(i.sources.join(", "))}</span></div>`).join("");
  const rooms = e.rooms.map((r) => `<tr><td>${esc(r.family)}</td><td>${esc(r.supplier)}</td><td>${esc(r.name)}</td><td>${r.occupancy}</td><td>${esc(r.bed)}</td><td>${r.size_sqm} m²${r.size_unit === "sqft" ? ` <span class="src">(${r.size} sqft)</span>` : ""}</td><td>${esc(r.view)}</td></tr>`).join("");
  const rel = e.room_pairs.filter((x) => x.relation !== "distinct" || x.differences.length <= 2)
    .map((x) => `<li><strong>${esc(x.relation)}</strong>: ${esc(x.a)} ↔ ${esc(x.b)}. <span class="src">${esc([...x.reasons, ...x.differences].join("; "))}</span></li>`).join("");
  return `<div class="card"><h2>${esc(e.name)}</h2><div class="meta"><span>${esc(e.area)}</span><span>${e.records.length} supplier records → 1 property</span><span class="mono">${esc(e.records.join(" · "))}</span></div></div>
  <div class="card"><h4>Sourced content</h4>${fieldsBlock(e)}</div>
  <div class="card"><h4>Gallery · ${e.content.images.length} unique, ${e.content.images_removed_as_duplicates} duplicate${e.content.images_removed_as_duplicates === 1 ? "" : "s"} removed</h4><div class="gallery">${imgs}</div></div>
  <div class="card"><h4>Room mapping</h4><table><thead><tr><th>Family</th><th>Supplier</th><th>Supplier label</th><th>Occ.</th><th>Bed</th><th>Size</th><th>View</th></tr></thead><tbody>${rooms}</tbody></table>
  <ul class="reasons">${rel}</ul></div>`;
}

function experienceDetail(e) {
  const c = e.config;
  const names = e.supplier_names.map((s) => `<li>${esc(s.supplier)}: “${esc(s.name)}”</li>`).join("");
  const related = (e.related || []).map((r) => `<li><strong>${esc(r.name)}</strong>: kept separate because ${esc(r.why_separate.join("; "))}</li>`).join("");
  return `<div class="card"><h2>${esc(e.name)}</h2><div class="meta"><span>${esc(e.area)}</span><span>operator: ${esc(e.operator || "not supplied")}</span><span class="mono">${esc(e.records.join(" · "))}</span></div></div>
  <div class="card"><h4>Configuration (preserved, never merged away)</h4><dl class="fields">
    <dt>Transfer</dt><dd>${c.pickup ? "hotel pickup included" : "self-transfer, no pickup"}</dd>
    <dt>Meal</dt><dd>${c.meal ? "included" : "not included"}</dd><dt>Duration</dt><dd>${c.duration_h} h</dd>
    <dt>Access</dt><dd>${esc(c.access)}</dd><dt>Time slot</dt><dd>${esc(c.slot)}</dd><dt>Language</dt><dd>${esc(c.language || "not supplied")}</dd></dl></div>
  <div class="card"><h4>Same product, ${e.supplier_names.length} supplier name${e.supplier_names.length > 1 ? "s" : ""}</h4><ul class="reasons">${names}</ul>
  ${related ? `<h4 style="margin-top:20px">Same attraction, different product</h4><ul class="reasons">${related}</ul>` : ""}</div>`;
}

function offersTable(e) {
  const hotel = e.vertical === "hotels";
  const rows = e.offers.map((o) => `<tr class="${o.eligible ? "" : "ineligible"}">
    <td>${esc(o.supplier)}</td>
    ${hotel ? `<td>${esc(o.family)}<br><span class="src">${esc(o.room_name)} · ${esc(o.meal)}</span></td>` : ""}
    <td><strong>${aed(o.total_aed)}</strong>${o.converted ? `<br><span class="src">${esc(o.currency)} ${o.total} at FX snapshot</span>` : ""}${o.taxes_included ? "" : `<br><span class="badge warn">taxes not included</span>`}</td>
    <td>${esc(o.policy_label)}<br><span class="src">${esc(o.payment)}</span></td>
    <td>${o.hours_old} h old<br><span class="src">${esc(o.reliability.label)}</span></td>
    <td>${o.eligible ? (o.labels.length ? `<span class="badge">${esc(o.labels.join(" · "))}</span>` : "eligible") : esc(o.ineligible_reasons.join("; "))}</td></tr>`).join("");
  return `<div class="card"><h4>Supplier offers${hotel ? " · labels compare within a room family only" : ""}</h4>
  <table><thead><tr><th>Supplier</th>${hotel ? "<th>Room</th>" : ""}<th>Stay total</th><th>Policy</th><th>Freshness · reliability</th><th>Decision</th></tr></thead><tbody>${rows}</tbody></table>
  <p class="caption" style="margin-top:12px">Cheapest comparable = lowest complete, eligible total. Unknown policies and tax-exclusive prices are never called cheapest or flexible.</p></div>`;
}

function reviewNote(e) {
  if (!e.review_pairs.length) return "";
  return `<div class="card"><h4>Possible duplicate awaiting review</h4><ul class="reasons">${e.review_pairs.map((d) => `<li>${esc(d.a)} ↔ ${esc(d.b)}: ${esc([...d.evidence, ...d.conflicts].join("; "))}</li>`).join("")}</ul><a class="link-btn" href="#review">Open review queue →</a></div>`;
}

// ---------------------------------------------------------------- raw feed baseline
async function showRaw() {
  const blocks = await Promise.all(["hotels", "experiences"].map(async (v) => {
    const rows = await api("/api/raw/" + v);
    return `<div class="card"><h4>${v === "hotels" ? "Hotels" : "Sightseeing"} · ${rows.length} listings</h4><ol class="reasons">${rows.map((r) => `<li>${esc(r.name)} <span class="src">${esc(r.supplier)} · ${esc(r.area)} · ${esc(r.id)}</span></li>`).join("")}</ol></div>`;
  }));
  $("#raw").innerHTML = blocks.join("") + `<div class="card"><h4>What changes</h4><p>The same Marina Pearl appears three times under three names; the Red Dune safari twice. SupplyLens shows each once, with every supplier offer still available inside it, and keeps look-alikes such as the self-transfer safari and the Jumeirah branch separate.</p><a class="link-btn" href="#search?v=hotels">See consolidated search →</a></div>`;
}

// ---------------------------------------------------------------- review queue
async function showReview() {
  const { queue, audit } = await api("/api/review");
  const side = (r) => `<div><strong>${esc(r.name)}</strong><br><span class="src">${esc(r.supplier)} · ${esc(r.id)}</span><br><span style="font-size:16px">${esc(r.address || r.area)}${r.operator !== undefined ? ` · operator: ${esc(r.operator || "not supplied")}` : ""}${r.phone !== undefined ? ` · phone: ${esc(r.phone || "not supplied")}` : ""}</span></div>`;
  $("#queue").innerHTML = queue.map((d) => `<div class="card" style="margin-bottom:8px">
    <p class="status">${d.reviewed ? `Reviewed: ${d.decision === "match" ? "same product" : "kept separate"}` : "Awaiting review"} · machine said ${esc(d.machine)} · ${d.vertical}</p>
    <div class="pair">${side(d.a_record)}${side(d.b_record)}</div>
    <p style="font-size:16px;margin-bottom:0"><strong>Evidence:</strong> ${esc(d.evidence.join("; "))}${d.conflicts.length ? `<br><strong>Conflicts:</strong> ${esc(d.conflicts.join("; "))}` : ""}</p>
    <div class="pair-actions">
      <button data-v="${d.vertical}" data-a="${esc(d.a)}" data-b="${esc(d.b)}" data-d="match">Same product</button>
      <button data-v="${d.vertical}" data-a="${esc(d.a)}" data-b="${esc(d.b)}" data-d="distinct">Keep separate</button>
      ${d.reviewed ? `<button data-v="${d.vertical}" data-a="${esc(d.a)}" data-b="${esc(d.b)}" data-d="reset">Undo</button>` : ""}
    </div></div>`).join("") || `<div class="card">Queue empty.</div>`;
  $("#audit").innerHTML = audit.map((a) => `<li>${esc(a.at)} ${esc(a.vertical)} ${esc(a.pair.join(" ↔ "))}: ${esc(a.from || "machine")} → ${esc(a.to || "machine")}</li>`).join("") || "<li>No decisions yet.</li>";
}
$("#queue").addEventListener("click", async (ev) => {
  const b = ev.target.closest("button[data-d]");
  if (!b) return;
  await api("/api/review", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ vertical: b.dataset.v, a: b.dataset.a, b: b.dataset.b, decision: b.dataset.d }) });
  showReview();
});

// ---------------------------------------------------------------- evidence
const pct = (x) => (x == null ? "N/A" : (x * 100).toFixed(0) + "%");
async function showEvidence() {
  const r = await api("/api/eval");
  $("#eval").innerHTML = Object.entries(r.verticals).map(([v, d]) => {
    const m = d.matching, s = d.ranking.summary;
    const mrow = (k, label) => `<tr><td>${label}</td><td>${m[k].auto_links}</td><td>${pct(m[k].auto_link_precision)}</td><td>${pct(m[k].auto_only_recall)}</td><td>${pct(m[k].assisted_recall)}</td><td>${m[k].sent_to_review}</td><td><strong>${m[k].harmful_merges}</strong></td></tr>`;
    const harmful = m.name_only_baseline.harmful_merge_examples.map((x) => `<li>${esc(x)}</li>`).join("");
    const intents = d.ranking.intents.map((i) => `<tr><td>${i.split}</td><td>${esc(i.query)}</td><td>${i.k}</td><td>${i.raw_supplier_order ?? "N/A"}</td><td>${i.cheapest_eligible ?? "N/A"}</td><td><strong>${i.supplylens ?? "N/A"}</strong></td></tr>`).join("");
    return `<h2 class="section-title">${v === "hotels" ? "Hotels" : "Sightseeing"}</h2>
    <div class="ev-grid">
      <div class="card"><h4>Identity matching · ${m.supplylens.pairs} labelled pairs, ${m.supplylens.true_matches} true matches</h4>
        <table><thead><tr><th>Method</th><th>Auto-links</th><th>Precision</th><th>Auto recall</th><th>Assisted recall</th><th>Review</th><th>Harmful merges</th></tr></thead>
        <tbody>${mrow("name_only_baseline", "Name-only baseline")}${mrow("supplylens", "SupplyLens")}</tbody></table>
        <p class="caption" style="margin-top:12px">Candidate recall ${pct(m.candidate_recall)}. Assisted recall counts review-queue pairs as found, assuming a correct reviewer.</p>
        ${harmful ? `<p style="font-size:16px"><strong>Baseline harmful merges:</strong></p><ul class="reasons">${harmful}</ul>` : ""}</div>
      <div class="card"><h4>Offer safety and speed</h4>
        <p class="big">${d.offers.rule_violations.length}</p><p style="font-size:16px">recommended offers violating eligibility, tax, freshness or availability rules, out of ${d.offers.recommendations_checked} checked.</p>
        <p class="big">${d.latency.p95_ms} ms</p><p style="font-size:16px">p95 search latency in-process (${d.latency.runs} warm runs, median ${d.latency.median_ms} ms). Excludes network.</p></div>
    </div>
    <div class="card" style="margin-top:8px"><h4>Listing ranking · mean NDCG@k (validation ${s.validation_intents_scored} intents, held-out test ${s.test_intents_scored} intents)</h4>
      <table><thead><tr><th>Split</th><th>Raw supplier order</th><th>Cheapest eligible</th><th>SupplyLens</th></tr></thead><tbody>
      <tr><td>validation (used for design)</td><td>${s.validation_raw_supplier_order_mean_ndcg}</td><td>${s.validation_cheapest_eligible_mean_ndcg}</td><td><strong>${s.validation_supplylens_mean_ndcg}</strong></td></tr>
      <tr><td>test (held out)</td><td>${s.test_raw_supplier_order_mean_ndcg}</td><td>${s.test_cheapest_eligible_mean_ndcg}</td><td><strong>${s.test_supplylens_mean_ndcg}</strong></td></tr></tbody></table>
      <details style="margin-top:12px"><summary class="caption">Per-intent results</summary><table><thead><tr><th>Split</th><th>Query</th><th>k</th><th>Raw</th><th>Cheapest</th><th>SupplyLens</th></tr></thead><tbody>${intents}</tbody></table></details></div>`;
  }).join("") + `<p class="caption" style="margin-top:24px">${esc(r.dataset)}. Every number is computed live from the code in this deployment.</p>`;
}

window.addEventListener("hashchange", route);
route();
