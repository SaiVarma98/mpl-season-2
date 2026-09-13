"""Local MPL auction-flow verification without touching production data.

Run from the project root:
    python scripts/verify_auction_flow.py
"""
from copy import deepcopy
import json
from pathlib import Path

from services.auction_engine import AuctionEngine
from services.sale_service import SaleService
from services.lot_flow_service import LotFlowService
from services.lifecycle_service import LifecycleService
from services.rollback_service import rollback_last_sale

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))

def docs():
    return {
        "players": load("players.json"),
        "teams": load("teams.json"),
        "groups": load("auction_groups.json"),
        "state": load("auction_state.json"),
    }

def result(r):
    d = r["data"]
    return {
        "players": d["players"],
        "teams": d["teams"],
        "groups": d.get("groups", d.get("auction_groups")),
        "state": d.get("state", d.get("auction_state")),
    }

def check(condition, message):
    if not condition:
        raise AssertionError(message)

def main():
    d = docs()

    d = result(AuctionEngine(**d).start())
    d = result(AuctionEngine(**d).select_group("G001"))
    check(d["state"]["current_bid"]["amount"] == 500, "Lot did not open at base price.")

    d = result(AuctionEngine(**d).bid("T001"))
    check(d["state"]["current_bid"] == {"amount": 500, "team_id": "T001"},
          "First bid is not exactly base price.")

    d = result(AuctionEngine(**d).set_increment(1000))
    d = result(AuctionEngine(**d).bid("T002"))
    check(d["state"]["current_bid"] == {"amount": 1500, "team_id": "T002"},
          "Configured increment was not applied server-side.")

    d = result(SaleService(**d).sell())
    team = next(t for t in d["teams"] if t["id"] == "T002")
    player = next(p for p in d["players"] if p["id"] == 1)
    group = next(g for g in d["groups"] if g["group_id"] == "G001")
    check(team["purse"] == 98500, "Winning-team purse is incorrect.")
    check(team["players"] == [1], "Winning team did not receive the player.")
    check(player["status"] == "sold" and player["team_id"] == "T002",
          "Player sale state is incorrect.")
    check(group["status"] == "sold" and group["winner_team_id"] == "T002",
          "Group sale state is incorrect.")

    # New lot must be selectable immediately after SOLD.
    d = result(AuctionEngine(**d).select_group("G002"))
    check(d["state"]["auction_status"] == "LIVE_BIDDING",
          "Next lot cannot be selected after SOLD.")
    check(d["state"]["current_bid"]["amount"] == 1000 and d["state"]["current_bid"]["team_id"] is None,
          "Next lot did not reopen at its base price.")

    d["groups"], d["state"] = (
        (lambda x: (x["data"]["groups"], x["data"]["auction_state"]))
        (LotFlowService(d["groups"], d["state"]).pass_lot())
    )
    check(d["state"]["auction_status"] == "WAITING_FOR_GROUP", "PASS failed.")

    # Pause/resume.
    d = result(AuctionEngine(**d).select_group("G002"))
    d = result(LifecycleService(**d).pause())
    check(d["state"]["auction_status"] == "PAUSED", "PAUSE failed.")
    d = result(LifecycleService(**d).resume())
    check(d["state"]["auction_status"] == "LIVE_BIDDING", "RESUME failed.")

    # Rollback an isolated sale.
    x = docs()
    x = result(AuctionEngine(**x).start())
    x = result(AuctionEngine(**x).select_group("G001"))
    x = result(AuctionEngine(**x).bid("T001"))
    x = result(SaleService(**x).sell())
    rb = rollback_last_sale(x["state"])["data"]
    check(next(t for t in rb["teams"] if t["id"] == "T001")["purse"] == 100000,
          "ROLLBACK did not restore purse.")
    check(next(p for p in rb["players"] if p["id"] == 1)["status"] == "available",
          "ROLLBACK did not restore player.")
    check(next(g for g in rb["auction_groups"] if g["group_id"] == "G001")["status"] == "pending",
          "ROLLBACK did not restore group.")

    print("MPL auction service flow: PASS")

if __name__ == "__main__":
    main()
