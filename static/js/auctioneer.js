
const state = {
  data: null,
  teams: [],
  groups: [],
  selectedTeam: null,
  bidIncrement: 1000,
  online: true
};

const $ = (id) => document.getElementById(id);

function money(n) {
  return new Intl.NumberFormat("en-IN", {style:"currency", currency:"INR", maximumFractionDigits:0}).format(Number(n || 0));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"
  }[c]));
}

function toast(message, good=true) {
  $("toast").innerHTML = `<div class="alert ${good ? "alert-success" : "alert-error"} shadow-xl"><span>${escapeHtml(message)}</span></div>`;
  setTimeout(() => $("toast").innerHTML = "", 3000);
}

async function api(url, options={}) {
  try {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: {"Content-Type":"application/json", ...(options.headers || {})},
      ...options
    });
    const payload = await response.json();
    if (!response.ok || payload.success === false) throw new Error(payload.message || "Request failed");
    state.online = true;
    setConnection();
    return payload;
  } catch (err) {
    state.online = false;
    setConnection();
    throw err;
  }
}

function setConnection() {
  $("connectionBadge").textContent = state.online ? "ONLINE" : "RECONNECTING";
  $("connectionBadge").className = `badge gap-2 ${state.online ? "badge-success" : "badge-error"}`;
  const b=$("offlineBanner"); if(b) b.classList.toggle("hidden", state.online);
}

function currentState() {
  return state.data?.state || {};
}

function renderLot() {
  const s = currentState();
  const group = state.groups.find(g => String(g.group_id) === String(s.current_group_id));
  const grid = $("playerGrid");

  if (!group) {
    $("lotTitle").textContent = s.auction_status === "COMPLETED" ? "Auction Completed" :
      s.auction_status === "PAUSED" ? "Auction Paused" : "Waiting for Next Lot";
    $("lotType").textContent = "—";
    grid.innerHTML = `<div class="player-placeholder sm:col-span-2 xl:col-span-3">${escapeHtml(s.auction_status || "WAITING")}</div>`;
    return;
  }

  $("lotTitle").textContent = `${group.group_id} • ${group.players?.length || 0} Player Lot`;
  $("lotType").textContent = String(group.type || "LOT").toUpperCase();

  const players = state.data.players || [];
  grid.innerHTML = (group.players || []).map(pid => {
    const p = players.find(x => String(x.id) === String(pid));
    if (!p) return `<div class="player-placeholder">PLAYER NOT FOUND</div>`;
    return `<article class="player-card">
      <img src="${escapeHtml(p.photo_url || "")}" alt="${escapeHtml(p.name)}"
           onerror="this.style.opacity='.2'">
      <div class="p-4">
        <div class="text-xl font-black">${escapeHtml(p.name)}</div>
        <div class="mt-2 flex flex-wrap gap-2">
          <span class="badge badge-outline">${escapeHtml(p.skill)}</span>
          <span class="badge badge-outline">${escapeHtml(p.handedness)}</span>
          <span class="badge badge-outline">Age ${escapeHtml(p.age)}</span>
        </div>
        <div class="mt-3 text-sm text-white/50">BASE PRICE</div>
        <div class="text-xl font-black text-amber-300">${money(group.base_price)}</div>
      </div>
    </article>`;
  }).join("");
}

function renderBid() {
  const s = currentState();
  const bid = s.current_bid || {};
  $("currentBid").textContent = money(bid.amount);
  const team = state.teams.find(t => String(t.id) === String(bid.team_id));
  $("leadingTeam").textContent = team ? team.team_name : "NO LEADING TEAM";
  const increment = Number(s.bid_increment || state.bidIncrement || 1000);
  state.bidIncrement = increment;
  $("incrementBadge").textContent = `+ ${money(increment)}`;
  $("customIncrement").value = increment;
  $("openingBidHint").textContent = team ? `NEXT BID • + ${money(increment)}` : "OPENING BID • BASE PRICE";
}

function renderTeams() {
  const bid = currentState().current_bid || {};
  $("teamGrid").innerHTML = state.teams.map(t => {
    const purse = Number(t.purse || 0);
    const def = Number(t.default_purse || 100000);
    const pct = Math.max(0, Math.min(100, purse / def * 100));
    const leading = String(t.id) === String(bid.team_id);
    const barClass = pct < 25 ? "purse-low" : pct <= 50 ? "purse-mid" : "";
    const can = currentState().auction_status === "LIVE_BIDDING";
    return `<button class="team-card auction-card p-4 text-left ${leading ? "leading" : ""}"
      onclick="selectTeam('${escapeHtml(t.id)}')" ${can ? "" : "disabled"}>
      <div class="flex items-center gap-3">
        <img class="team-logo" src="${escapeHtml(t.logo || "")}" alt="">
        <div class="min-w-0">
          <div class="truncate text-lg font-black">${escapeHtml(t.team_name)}</div>
          <div class="text-xs text-white/50">${escapeHtml(t.owner || "")}</div>
        </div>
      </div>
      <div class="mt-4 flex justify-between text-sm">
        <span class="text-white/50">PURSE</span><b>${money(purse)}</b>
      </div>
      <div class="purse-bar ${barClass} mt-2"><div style="width:${pct}%"></div></div>
      <div class="mt-3 flex justify-between text-xs text-white/50">
        <span>${(t.players || []).length} players</span>
        <span>${money(def - purse)} spent</span>
      </div>
      ${leading ? '<div class="mt-3 badge badge-warning">LEADING</div>' : '<div class="mt-3 badge badge-outline">CLICK TO BID</div>'}
    </button>`;
  }).join("");
}

window.selectTeam = async function(teamId) {
  if (currentState().auction_status !== "LIVE_BIDDING") {
    return toast("No live lot is open.", false);
  }
  state.selectedTeam = teamId;
  await bid();
};


async function setBidIncrement(value) {
  const n = Number(value);
  if (!Number.isFinite(n) || n < 50 || n % 50 !== 0) {
    toast("Bid increment must be a multiple of ₹50.", false);
    return false;
  }
  try {
    await api("/api/auction/increment", {
      method: "POST",
      body: JSON.stringify({increment: n})
    });
    state.bidIncrement = n;
    $("customIncrement").value = n;
    $("incrementBadge").textContent = `+ ${money(n)}`;
    document.querySelectorAll(".increment-btn").forEach(b => {
      b.classList.toggle("btn-warning", Number(b.dataset.inc) === n);
    });
    return true;
  } catch (e) {
    toast(e.message, false);
    return false;
  }
}

async function bid() {
  if (!state.selectedTeam) return toast("Select a team.", false);
  try {
    await api("/api/auction/bid", {method:"POST", body:JSON.stringify({team_id:state.selectedTeam})});
    await refresh();
  } catch(e) { toast(e.message, false); }
}

function renderGroups() {
  const s = currentState();
  const round = Number(s.current_round || 1);
  const query = String($("groupSearch")?.value || "").trim().toLowerCase();
  const normalize = v => String(v || "").toLowerCase().replace(/^g0*/, "");
  const groups = state.groups.filter(g => {
    const status=String(g.status||"").toLowerCase();
    if (Number(g.round)!==round || ["sold","invalid","completed"].includes(status)) return false;
    if (!query) return true;
    const gid=String(g.group_id||"").toLowerCase();
    return gid.includes(query) || normalize(gid).includes(normalize(query));
  });
  $("groupList").innerHTML = groups.length ? groups.map(g => `
    <button class="auction-card p-3 text-left hover:border-amber-300/60"
      onclick="selectGroup('${escapeHtml(g.group_id)}')">
      <div class="flex justify-between">
        <b>${escapeHtml(g.group_id)}</b>
        <span class="badge badge-sm">${escapeHtml(g.type || "")}</span>
      </div>
      <div class="mt-2 text-sm text-white/60">${(g.players || []).length} players</div>
      <div class="mt-1 font-black text-amber-300">${money(g.base_price)}</div>
      <div class="mt-1 text-xs uppercase text-white/40">${escapeHtml(g.status)}</div>
    </button>`).join("") :
    `<div class="text-white/40">No available groups in Round ${round}.</div>`;
}

window.selectGroup = async function(groupId) {
  try {
    await api("/api/auction/select", {method:"POST", body:JSON.stringify({group_id:groupId})});
    await refresh();
  } catch(e) { toast(e.message, false); }
};

function renderHistory() {
  const history = currentState().history || [];
  $("historyList").innerHTML = history.slice().reverse().slice(0,50).map(h => `
    <div class="event-row rounded-lg bg-white/[.03] p-3">
      <div class="flex justify-between text-xs text-white/40">
        <span>${escapeHtml(h.timestamp)}</span><span>${escapeHtml(h.event)}</span>
      </div>
      <div class="mt-1 text-sm">
        ${escapeHtml(h.group_id || "")}
        ${h.team_id ? " • " + escapeHtml(h.team_id) : ""}
        ${h.amount ? " • " + money(h.amount) : ""}
      </div>
    </div>`).join("") || `<div class="text-white/40">No history yet.</div>`;
}

function renderStats() {
  const stats = state.stats || {};
  const items = [
    ["Registered", stats.registered_players],
    ["Sold", stats.sold_players],
    ["Available", stats.available_players],
    ["Held Lots", stats.held_lots],
    ["Round 2", stats.round2_players],
    ["Highest Sale", money(stats.highest_sale)],
    ["Spent", money(stats.total_money_spent)]
  ];
  $("statsGrid").innerHTML = items.map(([k,v]) =>
    `<div class="rounded-xl bg-white/[.04] p-3"><div class="text-xs text-white/40">${k}</div><div class="mt-1 font-black">${v ?? "—"}</div></div>`
  ).join("");
}

function renderAll() {
  const s = currentState();
  $("stateBadge").textContent = s.auction_status || "—";
  $("roundBadge").textContent = `ROUND ${s.current_round || 1}`;
  renderLot(); renderBid(); renderTeams(); renderGroups(); renderHistory(); renderStats();
}

document.addEventListener("DOMContentLoaded",()=>{
  const input=$("groupSearch"), clear=$("clearGroupSearch");
  if(input){input.addEventListener("input",renderGroups); input.addEventListener("keydown",e=>{if(e.key==="Enter"){e.preventDefault(); const first=$("groupList")?.querySelector("button[onclick]"); if(first) first.click();}});}
  if(clear) clear.addEventListener("click",()=>{if(input){input.value="";renderGroups();input.focus();}});
});

async function refresh() {
  try {
    const [stateRes, playersRes, groupsRes, statsRes] = await Promise.all([
      api("/api/state"), api("/api/players"), api("/api/groups"), api("/api/statistics")
    ]);
    state.data = {
      ...stateRes.data,
      players: playersRes.data
    };
    state.teams = stateRes.data.teams || [];
    state.groups = groupsRes.data || [];
    state.stats = statsRes.data || {};
    renderAll();
  } catch(e) {
    // Keep the last good DOM on transient failure.
  }
}

async function action(url, body=null, confirmText=null) {
  if (confirmText && !window.confirm(confirmText)) return;
  try {
    await api(url, {method:"POST", body:body ? JSON.stringify(body) : undefined});
    toast("Operation completed.");
    await refresh();
  } catch(e) { toast(e.message, false); }
}

document.querySelectorAll(".increment-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    await setBidIncrement(Number(btn.dataset.inc));
  });
});
$("customIncrement").addEventListener("change", async () => {
  await setBidIncrement($("customIncrement").value);
});
$("sellBtn").addEventListener("click", () => action("/api/auction/sell", null, "Sell the current lot?"));
$("passBtn").addEventListener("click", () => action("/api/auction/pass"));
$("holdBtn").addEventListener("click", () => action("/api/auction/hold"));
$("pauseBtn").addEventListener("click", () => action("/api/auction/pause"));
$("resumeBtn").addEventListener("click", () => action("/api/auction/resume"));
$("startBtn").addEventListener("click", () => action("/api/auction/start"));
$("round2Btn").addEventListener("click", () => action("/api/auction/round2"));
$("rollbackBtn").addEventListener("click", () => action("/api/auction/rollback", {confirm:true}, "Rollback the last completed sale?"));
$("resetBtn").addEventListener("click", () => action("/api/auction/reset", {confirm:true}, "RESET the entire auction? This cannot be undone from the dashboard."));
$("endBtn").addEventListener("click", () => action("/api/auction/end", {confirm:true}, "END the auction?"));
$("refreshGroupsBtn").addEventListener("click", refresh);
$("logoutBtn").addEventListener("click", async () => {
  await fetch("/api/auth/logout", {method:"POST"});
  location.href="/login";
});

refresh();
setInterval(refresh, 500);


const restartLotBtn = document.getElementById("restartLotBtn");
if (restartLotBtn) {
  restartLotBtn.addEventListener("click", async () => {
    if (!confirm("Restart the current unsold lot at its base price? Current bid and leading team will be cleared.")) return;
    try {
      await api("/api/auction/restart-lot", { method: "POST", body: JSON.stringify({confirm:true}) });
      await refresh();
      toast("Current lot restarted at base price.", true);
    } catch (e) { toast(e.message, false); }
  });
}
