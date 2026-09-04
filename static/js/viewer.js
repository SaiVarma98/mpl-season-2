const viewer = {
  media:{tournament:{},sponsors:[],videos:[]},
  lastMode:null,lastState:null,lastSoldKey:null,soldUntil:0,videoTimer:null,sponsorIndex:0
};
const $=id=>document.getElementById(id);
function money(n){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(Number(n||0));}
function esc(v){return String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
async function getJSON(url){const r=await fetch(url,{cache:"no-store"});const d=await r.json();if(!r.ok||d.success===false)throw new Error(d.message||"Request failed");return d;}
function setScreen(mode){["waitingScreen","liveScreen","soldScreen","soldSummaryScreen","pausedScreen","completedScreen"].forEach(id=>$(id).hidden=true);const map={waiting:"waitingScreen",live:"liveScreen",sold:"soldScreen",paused:"pausedScreen",completed:"completedScreen"};if(map[mode])$(map[mode]).hidden=false;viewer.lastMode=mode;}
function showConnection(ok){$("connectionLost").hidden=ok;}
function applyBranding(){const t=viewer.media.tournament||{};if(t.name){document.title=`${t.name} — Season ${t.season||2}`;}const logo=t.main_logo_url;if(logo){$("brand-mark").innerHTML=`<img src="${esc(logo)}" alt="MPL">`;}}
function sponsorHTML(s){return `<div class="sponsor">${s.logo_url?`<img src="${esc(s.logo_url)}" alt="${esc(s.name||"")}">`:`<span>${esc(s.name||"")}</span>`}</div>`;}
function renderSponsors(){const a=viewer.media.sponsors||[];const left=$("sponsorLogosLeft"),right=$("sponsorLogosRight");const half=Math.ceil(a.length/2);const l=a.slice(0,half),r=a.slice(half);if(left)left.innerHTML=l.map(sponsorHTML).join("");if(right)right.innerHTML=r.map(sponsorHTML).join("");}
function playSponsorVideo(v){const el=$("sponsorVideo"),fb=$("sponsorVideoFallback");if(!el||!v)return;el.poster=v.poster_url||"";el.src=v.video_url;el.muted=true;el.loop=Boolean(v.loop);el.hidden=false;fb.hidden=true;el.play().catch(()=>{});clearTimeout(viewer.videoTimer);if(!v.loop){viewer.videoTimer=setTimeout(()=>{const vs=(viewer.media.videos||[]).filter(x=>x.enabled&&x.video_url);if(vs.length){viewer.sponsorIndex=(viewer.sponsorIndex+1)%vs.length;playSponsorVideo(vs[viewer.sponsorIndex]);}},Number(v.display_seconds||15)*1000);}}
function startSponsorRotation(){const vs=(viewer.media.videos||[]).filter(v=>v.enabled&&v.video_url);if(vs.length)playSponsorVideo(vs[0]);}
async function loadMedia(){try{const r=await getJSON("/api/viewer/media");viewer.media=r.data||viewer.media;applyBranding();renderSponsors();startSponsorRotation();}catch(e){}}
function groupFor(payload){return (payload.groups||[]).find(g=>String(g.group_id)===String(payload.state?.current_group_id));}
function renderLive(payload){
  const s=payload.state||{},g=groupFor(payload);
  if(!g){setScreen(s.auction_status==="PAUSED"?"paused":s.auction_status==="COMPLETED"?"completed":"waiting");return;}
  setScreen("live");
  $("groupLabel").textContent=g.group_id;
  $("lotType").textContent=String(g.type||"LOT").toUpperCase();
  $("basePrice").textContent=money(g.base_price);

  const players=payload.players||[],ids=g.players||[];
  const grid=$("playersGrid");
  grid.className=`players-grid ${ids.length===1?"single":ids.length===2?"duo":"trio"}`;
  grid.innerHTML=ids.map(pid=>{
    const p=players.find(x=>String(x.id)===String(pid));
    if(!p)return"";
    return `<article class="viewer-player">
      <img src="${esc(p.photo_url||"")}" alt="${esc(p.name)}" onerror="this.style.display='none'">
      <div class="player-meta">
        <div class="player-name">${esc(p.name)}</div>
        <div class="player-chips">
          <span class="player-chip">AGE ${esc(p.age)}</span>
          <span class="player-chip">${esc(p.skill)}</span>
          <span class="player-chip">${esc(p.handedness)}</span>
        </div>
      </div>
    </article>`;
  }).join("");

  const bid=s.current_bid||{},team=(payload.teams||[]).find(t=>String(t.id)===String(bid.team_id));
  $("currentBid").textContent=money(bid.amount||g.base_price);
  $("leadingTeam").textContent=team?team.team_name:"OPENING BID • BASE PRICE";

  $("teamSummary").innerHTML=(payload.teams||[]).map(t=>{
    const purchased=(t.players||[]).map(pid=>players.find(p=>String(p.id)===String(pid))).filter(Boolean);
    const playerNames=purchased.map(p=>esc(p.name)).join(" • ");
    return `<div class="team-mini ${String(t.id)===String(bid.team_id)?"leading":""}">
      <div class="team-mini-top">
        ${t.logo?`<img src="${esc(t.logo)}" alt="">`:``}
        <div class="team-mini-name">${esc(t.team_name)}</div>
        <div class="team-mini-purse">${money(t.purse)}</div>
      </div>
      <div class="team-mini-players">${purchased.length?playerNames:`<span class="team-no-players">No players yet</span>`}</div>
    </div>`;
  }).join("");
}
function renderSold(payload){
  const h=payload.state?.history||[];
  const sale=[...h].reverse().find(x=>x.event==="SOLD");
  if(!sale){setScreen("waiting");return;}

  const key=`${sale.timestamp}|${sale.group_id}|${sale.amount}|${(sale.players||[]).join(",")}`;
  if(viewer.lastSoldKey===key&&Date.now()>=viewer.soldUntil){setScreen("waiting");return;}

  viewer.lastSoldKey=key;
  viewer.soldUntil=Date.now()+4500;
  setScreen("sold");

  $("soldPrice").textContent=money(sale.amount);
  const t=(payload.teams||[]).find(x=>String(x.id)===String(sale.team_id));
  $("soldTeam").textContent=t?t.team_name:sale.team_id;

  const ps=payload.players||[];
  const soldPlayers=(sale.players||[]).map(id=>ps.find(x=>String(x.id)===String(id))).filter(Boolean);

  $("soldPlayers").textContent=soldPlayers.map(p=>p.name).join(" • ");

  const imageBox=$("soldPlayerImages");
  if(imageBox){
    imageBox.innerHTML=soldPlayers.map(p=>`
      <div class="sold-player-photo-card">
        <div class="sold-player-photo-wrap">
          <img src="${esc(p.photo_url||"")}" alt="${esc(p.name)}" onerror="this.style.display='none'">
        </div>
        <div class="sold-player-photo-name">${esc(p.name)}</div>
      </div>
    `).join("");
  }
}
function renderSoldSummary(payload){const grid=$("soldTeamGrid");if(!grid)return;const teams=payload.teams||[],players=payload.players||[],groups=payload.groups||[],sold=groups.filter(g=>String(g.status).toLowerCase()==="sold");grid.innerHTML=teams.map(t=>{const rows=sold.filter(g=>String(g.winner_team_id)===String(t.id)).flatMap(g=>(g.players||[]).map(pid=>{const p=players.find(x=>String(x.id)===String(pid));return p?{name:p.name,price:g.current_bid||0}:null;})).filter(Boolean);return `<article class="sold-team-card"><div class="sold-team-card-head">${t.logo?`<img src="${esc(t.logo)}" alt="">`:`<div class="sold-team-logo-fallback">${esc((t.team_name||"T").charAt(0))}</div>`}<div><div class="sold-team-name">${esc(t.team_name)}</div><div class="sold-team-count">${rows.length} player${rows.length===1?"":"s"}</div></div></div><div class="sold-player-list">${rows.length?rows.map(r=>`<div class="sold-player-row"><span>${esc(r.name)}</span><strong>${money(r.price)}</strong></div>`).join(""):`<div class="sold-empty">No players sold</div>`}</div></article>`;}).join("");}
function detectMode(p){const s=p.state||{};if(s.auction_finished||s.auction_status==="COMPLETED")return"completed";if(s.auction_status==="PAUSED")return"paused";if(s.auction_status==="LOT_SOLD")return"sold";if(s.auction_status==="LIVE_BIDDING")return"live";return"waiting";}
async function poll(){try{const [a,b]=await Promise.all([getJSON("/api/state"),getJSON("/api/players")]);const payload={...a.data,players:b.data,groups:a.data.groups||[],teams:a.data.teams||[]};showConnection(true);renderSoldSummary(payload);const mode=detectMode(payload);if(mode==="sold"){if(viewer.lastSoldKey===null||viewer.lastMode!=="sold"){renderSold(payload);}else if(Date.now()<viewer.soldUntil){return;}else{setScreen("waiting");}}else if(mode==="live"){renderLive(payload);}else if(mode==="waiting"){setScreen("waiting");$("waitingMessage").textContent="WAITING FOR NEXT LOT";const hasSold=(payload.groups||[]).some(g=>String(g.status).toLowerCase()==="sold");if(hasSold){$("waitingScreen").hidden=true;$("soldSummaryScreen").hidden=false;viewer.lastMode="waiting-summary";}}else setScreen(mode);viewer.lastState=payload;if(mode!=="sold")viewer.lastMode=mode;}catch(e){showConnection(false);}}
loadMedia();poll();setInterval(poll,500);
