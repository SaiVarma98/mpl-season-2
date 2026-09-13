const state = {
  data: null,
  teams: [],
  groups: [],
  selectedTeam: null,
  bidIncrement: 1000,
  online: true,

  // Performance / concurrency protection
  bidInProgress: false,
  refreshInFlight: false,
  localRevision: 0
};

const $ = (id) => document.getElementById(id);

function money(n) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0
  }).format(Number(n || 0));
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  }[c]));
}

function toast(message, good = true) {
  const toastEl = $("toast");

  if (!toastEl) return;

  toastEl.innerHTML = `
    <div class="alert ${good ? "alert-success" : "alert-error"} shadow-xl">
      <span>${escapeHtml(message)}</span>
    </div>
  `;

  setTimeout(() => {
    toastEl.innerHTML = "";
  }, 3000);
}

async function api(url, options = {}) {
  try {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {})
      },
      ...options
    });

    const payload = await response.json();

    if (!response.ok || payload.success === false) {
      throw new Error(payload.message || "Request failed");
    }

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
  const badge = $("connectionBadge");

  if (badge) {
    badge.textContent = state.online ? "ONLINE" : "RECONNECTING";
    badge.className = `badge gap-2 ${
      state.online ? "badge-success" : "badge-error"
    }`;
  }

  const banner = $("offlineBanner");

  if (banner) {
    banner.classList.toggle("hidden", state.online);
  }
}

function currentState() {
  return state.data?.state || {};
}

/* =========================================================
   LOT DISPLAY
   ========================================================= */

function renderLot() {
  const s = currentState();

  const group = state.groups.find(
    g => String(g.group_id) === String(s.current_group_id)
  );

  const grid = $("playerGrid");

  if (!grid) return;

  if (!group) {
    $("lotTitle").textContent =
      s.auction_status === "COMPLETED"
        ? "Auction Completed"
        : s.auction_status === "PAUSED"
          ? "Auction Paused"
          : "Waiting for Next Lot";

    $("lotType").textContent = "—";

    grid.innerHTML = `
      <div class="player-placeholder sm:col-span-2 xl:col-span-3">
        ${escapeHtml(s.auction_status || "WAITING")}
      </div>
    `;

    return;
  }

  $("lotTitle").textContent =
    `${group.group_id} • ${group.players?.length || 0} Player Lot`;

  $("lotType").textContent =
    String(group.type || "LOT").toUpperCase();

  const players = state.data?.players || [];

  grid.innerHTML = (group.players || [])
    .map(pid => {
      const p = players.find(
        x => String(x.id) === String(pid)
      );

      if (!p) {
        return `
          <div class="player-placeholder">
            PLAYER NOT FOUND
          </div>
        `;
      }

      return `
        <article class="player-card">
          <img
            src="${escapeHtml(p.photo_url || "")}"
            alt="${escapeHtml(p.name)}"
            onerror="this.style.opacity='.2'"
          >

          <div class="p-4">
            <div class="text-xl font-black">
              ${escapeHtml(p.name)}
            </div>

            <div class="mt-2 flex flex-wrap gap-2">
              <span class="badge badge-outline">
                ${escapeHtml(p.skill)}
              </span>

              <span class="badge badge-outline">
                ${escapeHtml(p.handedness)}
              </span>

              <span class="badge badge-outline">
                Age ${escapeHtml(p.age)}
              </span>
            </div>

            <div class="mt-3 text-sm text-white/50">
              BASE PRICE
            </div>

            <div class="text-xl font-black text-amber-300">
              ${money(group.base_price)}
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

/* =========================================================
   BID DISPLAY
   ========================================================= */

function renderBid() {
  const s = currentState();
  const bid = s.current_bid || {};

  const currentBidEl = $("currentBid");
  const leadingTeamEl = $("leadingTeam");

  if (currentBidEl) {
    currentBidEl.textContent = money(bid.amount);
  }

  const team = state.teams.find(
    t => String(t.id) === String(bid.team_id)
  );

  if (leadingTeamEl) {
    leadingTeamEl.textContent =
      team ? team.team_name : "NO LEADING TEAM";
  }

  const increment =
    Number(s.bid_increment || state.bidIncrement || 1000);

  state.bidIncrement = increment;

  const incrementBadge = $("incrementBadge");
  const customIncrement = $("customIncrement");
  const openingBidHint = $("openingBidHint");

  if (incrementBadge) {
    incrementBadge.textContent = `+ ${money(increment)}`;
  }

  if (customIncrement) {
    customIncrement.value = increment;
  }

  if (openingBidHint) {
    openingBidHint.textContent = team
      ? `NEXT BID • + ${money(increment)}`
      : "OPENING BID • BASE PRICE";
  }
}

/* =========================================================
   TEAM BUTTONS
   ========================================================= */

function renderTeams() {
  const bid = currentState().current_bid || {};
  const teamGrid = $("teamGrid");

  if (!teamGrid) return;

  teamGrid.innerHTML = state.teams
    .map(t => {
      const purse = Number(t.purse || 0);
      const def = Number(t.default_purse || 100000);

      const pct = Math.max(
        0,
        Math.min(100, purse / def * 100)
      );

      const leading =
        String(t.id) === String(bid.team_id);

      const barClass =
        pct < 25
          ? "purse-low"
          : pct <= 50
            ? "purse-mid"
            : "";

      const can =
        currentState().auction_status === "LIVE_BIDDING" &&
        !state.bidInProgress;

      return `
        <button
          class="team-card auction-card p-4 text-left ${
            leading ? "leading" : ""
          }"
          onclick="selectTeam('${escapeHtml(t.id)}')"
          ${can ? "" : "disabled"}
        >

          <div class="flex items-center gap-3">

            <img
              class="team-logo"
              src="${escapeHtml(t.logo || "")}"
              alt=""
            >

            <div class="min-w-0">

              <div class="truncate text-lg font-black">
                ${escapeHtml(t.team_name)}
              </div>

              <div class="text-xs text-white/50">
                ${escapeHtml(t.owner || "")}
              </div>

            </div>

          </div>

          <div class="mt-4 flex justify-between text-sm">
            <span class="text-white/50">PURSE</span>
            <b>${money(purse)}</b>
          </div>

          <div class="purse-bar ${barClass} mt-2">
            <div style="width:${pct}%"></div>
          </div>

          <div class="mt-3 flex justify-between text-xs text-white/50">
            <span>${(t.players || []).length} players</span>
            <span>${money(def - purse)} spent</span>
          </div>

          ${
            leading
              ? '<div class="mt-3 badge badge-warning">LEADING</div>'
              : '<div class="mt-3 badge badge-outline">CLICK TO BID</div>'
          }

        </button>
      `;
    })
    .join("");
}

/* =========================================================
   SELECT TEAM / BID
   ========================================================= */

window.selectTeam = async function(teamId) {

  if (currentState().auction_status !== "LIVE_BIDDING") {
    return toast("No live lot is open.", false);
  }

  // Prevent double-click / multiple bids
  if (state.bidInProgress) {
    return;
  }

  state.selectedTeam = teamId;

  await bid();
};

/* =========================================================
   BID INCREMENT
   ========================================================= */

async function setBidIncrement(value) {
  const n = Number(value);

  if (
    !Number.isFinite(n) ||
    n < 50 ||
    n % 50 !== 0
  ) {
    toast(
      "Bid increment must be a multiple of ₹50.",
      false
    );

    return false;
  }

  try {
    await api("/api/auction/increment", {
      method: "POST",
      body: JSON.stringify({
        increment: n
      })
    });

    state.bidIncrement = n;

    const customIncrement = $("customIncrement");

    if (customIncrement) {
      customIncrement.value = n;
    }

    const incrementBadge = $("incrementBadge");

    if (incrementBadge) {
      incrementBadge.textContent = `+ ${money(n)}`;
    }

    document
      .querySelectorAll(".increment-btn")
      .forEach(b => {
        b.classList.toggle(
          "btn-warning",
          Number(b.dataset.inc) === n
        );
      });

    return true;

  } catch (e) {

    toast(e.message, false);

    return false;
  }
}

/* =========================================================
   OPTIMIZED BID
   ========================================================= */

async function bid() {

  if (!state.selectedTeam) {
    return toast("Select a team.", false);
  }

  if (state.bidInProgress) {
    return;
  }

  state.bidInProgress = true;

  // Increment revision so an older refresh cannot overwrite
  // this bid result.
  const bidRevision = ++state.localRevision;

  // Disable team buttons immediately.
  renderTeams();

  try {

    const result = await api(
      "/api/auction/bid",
      {
        method: "POST",
        body: JSON.stringify({
          team_id: state.selectedTeam
        })
      }
    );

    /*
     * IMPORTANT:
     *
     * The bid endpoint deliberately returns a SMALL payload: just the
     * updated `state` and the single current `group` (players/teams
     * purses never change on a bid, only on SELL, so the backend never
     * sends full `teams`/`groups`/`players` arrays here). We patch the
     * one changed group into our local state.groups instead of waiting
     * for the next 2-second refresh() poll, so the lot list stays live.
     */

    if (result?.data) {

      // Update state if returned by backend.
      if (result.data.state) {
        state.data = {
          ...(state.data || {}),
          state: result.data.state
        };
      }

      // Patch the single updated group (current lot) into our cached
      // groups array so the lot-browser panel doesn't show a stale bid
      // amount until the next poll.
      if (result.data.group) {
        const updatedGroup = result.data.group;
        const idx = state.groups.findIndex(
          g => String(g.group_id) === String(updatedGroup.group_id)
        );
        if (idx !== -1) {
          state.groups[idx] = updatedGroup;
        } else {
          state.groups.push(updatedGroup);
        }
      }

      /*
       * Render immediately from the successful bid response.
       * No await refresh() here.
       */
      renderLot();
      renderBid();
      renderTeams();
      renderGroups();
      renderHistory();
      renderStats();
    }

  } catch (e) {

    toast(e.message, false);

  } finally {

    state.bidInProgress = false;

    /*
     * Re-render buttons after bid completes so they become
     * clickable again.
     */
    renderTeams();
  }
}

/* =========================================================
   GROUP SEARCH
   ========================================================= */

function renderGroups() {

  const s = currentState();

  const round = Number(
    s.current_round || 1
  );

  const searchInput = $("groupSearch");

  const query = String(
    searchInput?.value || ""
  )
    .trim()
    .toLowerCase();

  const normalize = v =>
    String(v || "")
      .toLowerCase()
      .replace(/^g0*/, "");

  const groups = state.groups.filter(g => {

    const status =
      String(g.status || "").toLowerCase();

    if (
      Number(g.round) !== round ||
      ["sold", "invalid", "completed"].includes(status)
    ) {
      return false;
    }

    if (!query) {
      return true;
    }

    const gid =
      String(g.group_id || "").toLowerCase();

    return (
      gid.includes(query) ||
      normalize(gid).includes(normalize(query))
    );
  });

  const groupList = $("groupList");

  if (!groupList) return;

  groupList.innerHTML = groups.length
    ? groups
        .map(g => `
          <button
            class="auction-card p-3 text-left hover:border-amber-300/60"
            onclick="selectGroup('${escapeHtml(g.group_id)}')"
          >

            <div class="flex justify-between">

              <b>${escapeHtml(g.group_id)}</b>

              <span class="badge badge-sm">
                ${escapeHtml(g.type || "")}
              </span>

            </div>

            <div class="mt-2 text-sm text-white/60">
              ${(g.players || []).length} players
            </div>

            <div class="mt-1 font-black text-amber-300">
              ${money(g.base_price)}
            </div>

            <div class="mt-1 text-xs uppercase text-white/40">
              ${escapeHtml(g.status)}
            </div>

          </button>
        `)
        .join("")
    : `
      <div class="text-white/40">
        No available groups in Round ${round}.
      </div>
    `;
}

/* =========================================================
   SELECT GROUP
   ========================================================= */

window.selectGroup = async function(groupId) {

  try {

    await api(
      "/api/auction/select",
      {
        method: "POST",
        body: JSON.stringify({
          group_id: groupId
        })
      }
    );

    await refresh();

  } catch (e) {

    toast(e.message, false);
  }
};

/* =========================================================
   HISTORY
   ========================================================= */

function renderHistory() {

  const history =
    currentState().history || [];

  const historyList = $("historyList");

  if (!historyList) return;

  historyList.innerHTML =
    history
      .slice()
      .reverse()
      .slice(0, 50)
      .map(h => `
        <div class="event-row rounded-lg bg-white/[.03] p-3">

          <div class="flex justify-between text-xs text-white/40">
            <span>
              ${escapeHtml(h.timestamp)}
            </span>

            <span>
              ${escapeHtml(h.event)}
            </span>
          </div>

          <div class="mt-1 text-sm">

            ${escapeHtml(h.group_id || "")}

            ${
              h.team_id
                ? " • " + escapeHtml(h.team_id)
                : ""
            }

            ${
              h.amount
                ? " • " + money(h.amount)
                : ""
            }

          </div>

        </div>
      `)
      .join("")
    ||
    `
      <div class="text-white/40">
        No history yet.
      </div>
    `;
}

/* =========================================================
   STATISTICS
   ========================================================= */

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

  const statsGrid = $("statsGrid");

  if (!statsGrid) return;

  statsGrid.innerHTML = items
    .map(([k, v]) => `
      <div class="rounded-xl bg-white/[.04] p-3">

        <div class="text-xs text-white/40">
          ${k}
        </div>

        <div class="mt-1 font-black">
          ${v ?? "—"}
        </div>

      </div>
    `)
    .join("");
}

/* =========================================================
   RENDER EVERYTHING
   ========================================================= */

function renderAll() {

  const s = currentState();

  const stateBadge = $("stateBadge");
  const roundBadge = $("roundBadge");

  if (stateBadge) {
    stateBadge.textContent =
      s.auction_status || "—";
  }

  if (roundBadge) {
    roundBadge.textContent =
      `ROUND ${s.current_round || 1}`;
  }

  renderLot();
  renderBid();
  renderTeams();
  renderGroups();
  renderHistory();
  renderStats();
}

/* =========================================================
   DOM READY
   ========================================================= */

document.addEventListener(
  "DOMContentLoaded",
  () => {

    const input = $("groupSearch");
    const clear = $("clearGroupSearch");

    if (input) {

      input.addEventListener(
        "input",
        renderGroups
      );

      input.addEventListener(
        "keydown",
        e => {

          if (e.key === "Enter") {

            e.preventDefault();

            const first =
              $("groupList")
                ?.querySelector(
                  "button[onclick]"
                );

            if (first) {
              first.click();
            }
          }
        }
      );
    }

    if (clear) {

      clear.addEventListener(
        "click",
        () => {

          if (input) {
            input.value = "";
            renderGroups();
            input.focus();
          }

        }
      );
    }
  }
);

/* =========================================================
   REFRESH
   ========================================================= */

async function refresh() {

  /*
   * Don't start another refresh if one is already running.
   *
   * This is important because the old application was polling
   * every 500ms and could start multiple refreshes at once.
   */
  if (state.refreshInFlight) {
    return;
  }

  state.refreshInFlight = true;

  /*
   * Remember the revision at the beginning of the request.
   *
   * If a bid happens while this refresh is running, the refresh
   * response is considered stale and will not overwrite the bid.
   */
  const revisionAtStart =
    state.localRevision;

  try {

    const [
      stateRes,
      playersRes,
      groupsRes,
      statsRes
    ] = await Promise.all([
      api("/api/state"),
      api("/api/players"),
      api("/api/groups"),
      api("/api/statistics")
    ]);

    /*
     * If a bid occurred while these requests were running,
     * don't overwrite the newer bid state.
     */
    if (
      revisionAtStart !== state.localRevision
    ) {
      return;
    }

    state.data = {
      ...stateRes.data,
      players: playersRes.data
    };

    state.teams =
      stateRes.data.teams || [];

    state.groups =
      groupsRes.data || [];

    state.stats =
      statsRes.data || {};

    renderAll();

  } catch (e) {

    /*
     * Keep the last good DOM on transient failure.
     */

  } finally {

    state.refreshInFlight = false;
  }
}

/* =========================================================
   GENERAL ACTIONS
   ========================================================= */

async function action(
  url,
  body = null,
  confirmText = null
) {

  if (
    confirmText &&
    !window.confirm(confirmText)
  ) {
    return;
  }

  try {

    await api(
      url,
      {
        method: "POST",
        body: body
          ? JSON.stringify(body)
          : undefined
      }
    );

    toast("Operation completed.");

    await refresh();

  } catch (e) {

    toast(e.message, false);
  }
}

/* =========================================================
   BID INCREMENT BUTTONS
   ========================================================= */

document
  .querySelectorAll(".increment-btn")
  .forEach(btn => {

    btn.addEventListener(
      "click",
      async () => {

        await setBidIncrement(
          Number(btn.dataset.inc)
        );

      }
    );

  });

const customIncrement =
  $("customIncrement");

if (customIncrement) {

  customIncrement.addEventListener(
    "change",
    async () => {

      await setBidIncrement(
        customIncrement.value
      );

    }
  );
}

/* =========================================================
   AUCTION ACTION BUTTONS
   ========================================================= */

const sellBtn = $("sellBtn");

if (sellBtn) {
  sellBtn.addEventListener(
    "click",
    () =>
      action(
        "/api/auction/sell",
        null,
        "Sell the current lot?"
      )
  );
}

const passBtn = $("passBtn");

if (passBtn) {
  passBtn.addEventListener(
    "click",
    () =>
      action("/api/auction/pass")
  );
}

const holdBtn = $("holdBtn");

if (holdBtn) {
  holdBtn.addEventListener(
    "click",
    () =>
      action("/api/auction/hold")
  );
}

const pauseBtn = $("pauseBtn");

if (pauseBtn) {
  pauseBtn.addEventListener(
    "click",
    () =>
      action("/api/auction/pause")
  );
}

const resumeBtn = $("resumeBtn");

if (resumeBtn) {
  resumeBtn.addEventListener(
    "click",
    () =>
      action("/api/auction/resume")
  );
}

const startBtn = $("startBtn");

if (startBtn) {
  startBtn.addEventListener(
    "click",
    () =>
      action("/api/auction/start")
  );
}

const round2Btn = $("round2Btn");

if (round2Btn) {
  round2Btn.addEventListener(
    "click",
    () =>
      action("/api/auction/round2")
  );
}

const rollbackBtn = $("rollbackBtn");

if (rollbackBtn) {

  rollbackBtn.addEventListener(
    "click",
    () =>
      action(
        "/api/auction/rollback",
        { confirm: true },
        "Rollback the last completed sale?"
      )
  );
}

const resetBtn = $("resetBtn");

if (resetBtn) {

  resetBtn.addEventListener(
    "click",
    () =>
      action(
        "/api/auction/reset",
        { confirm: true },
        "RESET the entire auction? This cannot be undone from the dashboard."
      )
  );
}

const endBtn = $("endBtn");

if (endBtn) {

  endBtn.addEventListener(
    "click",
    () =>
      action(
        "/api/auction/end",
        { confirm: true },
        "END the auction?"
      )
  );
}

const refreshGroupsBtn =
  $("refreshGroupsBtn");

if (refreshGroupsBtn) {

  refreshGroupsBtn.addEventListener(
    "click",
    refresh
  );
}

/* =========================================================
   LOGOUT
   ========================================================= */

const logoutBtn = $("logoutBtn");

if (logoutBtn) {

  logoutBtn.addEventListener(
    "click",
    async () => {

      await fetch(
        "/api/auth/logout",
        {
          method: "POST"
        }
      );

      location.href = "/login";
    }
  );
}

/* =========================================================
   INITIAL LOAD
   ========================================================= */

refresh();

/*
 * PERFORMANCE CHANGE:
 *
 * OLD:
 *   setInterval(refresh, 500);
 *
 * NEW:
 *   refresh every 2 seconds.
 *
 * The bid function no longer calls refresh() after every bid,
 * so a successful bid updates the UI immediately from its
 * response.
 */
setInterval(
  refresh,
  2000
);

/* =========================================================
   RESTART CURRENT LOT
   ========================================================= */

const restartLotBtn =
  document.getElementById(
    "restartLotBtn"
  );

if (restartLotBtn) {

  restartLotBtn.addEventListener(
    "click",
    async () => {

      if (
        !confirm(
          "Restart the current unsold lot at its base price? Current bid and leading team will be cleared."
        )
      ) {
        return;
      }

      try {

        await api(
          "/api/auction/restart-lot",
          {
            method: "POST",
            body: JSON.stringify({
              confirm: true
            })
          }
        );

        await refresh();

        toast(
          "Current lot restarted at base price.",
          true
        );

      } catch (e) {

        toast(
          e.message,
          false
        );
      }
    }
  );
}