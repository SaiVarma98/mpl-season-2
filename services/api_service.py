"""API-facing orchestration for the MPL auction.

This layer keeps Flask routes thin. It loads persisted documents, invokes the
appropriate domain service, and persists the returned documents.
"""

from copy import deepcopy

from repositories.auction_repository import AuctionRepository
from services.auction_engine import AuctionEngine, AuctionError
from services.sale_service import SaleService, SaleError
from services.rollback_service import rollback_last_sale, RollbackError
from services.lot_flow_service import LotFlowService, LotFlowError
from services.lifecycle_service import LifecycleService, LifecycleError
from storage.json_storage import transaction


class APIService:
    def __init__(self, repository):
        self.repository = repository

    def _engine(self):
        docs = self.repository.load_all()
        return AuctionEngine(
            docs["players"], docs["teams"], docs["groups"], docs["state"]
        )

    # Mutating methods wrap their full load -> mutate -> save sequence in
    # `transaction()` so the whole thing is a single critical section. This
    # closes off a real race (e.g. a bid and a sell landing back-to-back) if
    # this is ever served with threaded=True or multiple worker
    # processes/threads.
    #
    # Each one also only writes the JSON files it actually changed.
    # write_json() fsyncs to disk, and save_all() rewrites all four files
    # (players/teams/groups/state) whether or not they changed — on this
    # machine that's ~4ms per call vs ~1-2ms for a targeted write, and on
    # slower disks/network storage the gap is much bigger. Since most
    # auctioneer actions (start, select a lot, change increment, pause,
    # resume, end) never touch players or team purses, they should never
    # pay for writing those files. This is the main source of the latency
    # noticeable when selecting a lot or bidding.
    #
    # Read-only endpoints (state/players/groups/current_group/history/
    # statistics) are intentionally NOT wrapped in transaction() — they're
    # polled frequently by the auctioneer and viewer screens, and forcing
    # every poll through the same lock used for mutations adds contention
    # without adding real safety (stale-by-a-poll display data is harmless
    # and self-corrects on the next refresh).

    def start(self):
        with transaction():
            engine = self._engine()
            result = engine.start()
            # Only auction_state.json changes on start.
            self.repository.save_state(result["data"]["state"])
            return result

    def select(self, group_id):
        with transaction():
            engine = self._engine()
            result = engine.select_group(group_id)
            # Only the selected group + state change; players/teams are untouched.
            self.repository.save_groups_and_state(
                result["data"]["groups"], result["data"]["state"]
            )
            return result

    def restart_current_lot(self):
        with transaction():
            engine = self._engine()
            result = engine.restart_current_lot()
            self.repository.save_groups_and_state(
                result["data"]["groups"], result["data"]["state"]
            )
            return result

    def set_increment(self, increment):
        with transaction():
            engine = self._engine()
            result = engine.set_increment(increment)
            # Only auction_state.json changes.
            self.repository.save_state(result["data"]["state"])
            return result

    def set_auto_increment(self):
        with transaction():
            engine = self._engine()
            result = engine.set_auto_increment()
            # Only auction_state.json changes.
            self.repository.save_state(result["data"]["state"])
            return result

    def bid(self, team_id):
        # A bid only mutates live auction state and the current group's bid.
        # Players and team purses do not change until SELL, so avoid rewriting
        # those JSON files on every click. This substantially shortens the
        # critical path for rapid bidding.
        with transaction():
            engine = self._engine()
            result = engine.bid(team_id)
            data = result["data"]
            self.repository.save_groups_and_state(data["groups"], data["state"])

            # Keep the bid response intentionally small. The auctioneer already
            # has players/teams cached in memory and can update the changed fields
            # immediately without triggering four more GET requests.
            current_group_id = data["state"].get("current_group_id")
            current_group = next(
                (g for g in data["groups"] if str(g.get("group_id")) == str(current_group_id)),
                None,
            )
            return {
                "success": True,
                "message": result.get("message", "Bid accepted successfully."),
                "data": {
                    "state": data["state"],
                    "group": current_group,
                },
            }

    def sell(self):
        # Players, teams, groups and state all change on a sale — save_all
        # is correct (and necessary) here.
        with transaction():
            docs = self.repository.load_all()
            result = SaleService(
                docs["players"], docs["teams"], docs["groups"], docs["state"]
            ).sell()
            self.repository.save_all({
                "players": result["data"]["players"],
                "teams": result["data"]["teams"],
                "groups": result["data"]["auction_groups"],
                "state": result["data"]["auction_state"],
            })
            return result

    def rollback(self):
        # Restores a full pre-sale snapshot across all four documents.
        with transaction():
            docs = self.repository.load_all()
            result = rollback_last_sale(docs["state"])
            self.repository.save_all({
                "players": result["data"]["players"],
                "teams": result["data"]["teams"],
                "groups": result["data"]["auction_groups"],
                "state": result["data"]["auction_state"],
            })
            return result

    def pass_lot(self):
        with transaction():
            docs = self.repository.load_all()
            result = LotFlowService(docs["groups"], docs["state"]).pass_lot()
            self.repository.save_groups_and_state(
                result["data"]["groups"], result["data"]["auction_state"]
            )
            return result

    def hold_lot(self):
        with transaction():
            docs = self.repository.load_all()
            result = LotFlowService(docs["groups"], docs["state"]).hold_lot()
            self.repository.save_groups_and_state(
                result["data"]["groups"], result["data"]["auction_state"]
            )
            return result

    def pause(self):
        with transaction():
            docs = self.repository.load_all()
            result = LifecycleService(
                docs["players"], docs["teams"], docs["groups"], docs["state"]
            ).pause()
            # Only auction_state.json changes.
            self.repository.save_state(result["data"]["auction_state"])
            return result

    def resume(self):
        with transaction():
            docs = self.repository.load_all()
            result = LifecycleService(
                docs["players"], docs["teams"], docs["groups"], docs["state"]
            ).resume()
            # Only auction_state.json changes.
            self.repository.save_state(result["data"]["auction_state"])
            return result

    def round2(self):
        with transaction():
            docs = self.repository.load_all()
            result = LotFlowService(docs["groups"], docs["state"]).start_round_2()
            self.repository.save_groups_and_state(
                result["data"]["groups"], result["data"]["auction_state"]
            )
            return result

    def end(self):
        with transaction():
            docs = self.repository.load_all()
            result = LifecycleService(
                docs["players"], docs["teams"], docs["groups"], docs["state"]
            ).end()
            # Only auction_state.json changes.
            self.repository.save_state(result["data"]["auction_state"])
            return result

    def reset(self, backup_func):
        # A reset rewrites everything back to its starting values, plus takes
        # a backup first — save_all is correct here.
        with transaction():
            docs = self.repository.load_all()
            result = LifecycleService(
                docs["players"], docs["teams"], docs["groups"], docs["state"]
            ).reset(backup_func, confirm=True)
            self.repository.save_all({
                "players": result["data"]["players"],
                "teams": result["data"]["teams"],
                "groups": result["data"]["auction_groups"],
                "state": result["data"]["auction_state"],
            })
            return result

    def state(self):
        docs = self.repository.load_all()
        return {
            "success": True,
            "message": "Auction state loaded.",
            "data": {
                "state": docs["state"],
                "groups": docs["groups"],
                "teams": docs["teams"],
                "players": docs["players"],
            },
        }

    def players(self):
        players = self.repository.load_players()
        return {"success": True, "message": "Players loaded.", "data": players}

    def groups(self):
        groups = self.repository.load_groups()
        return {"success": True, "message": "Groups loaded.", "data": groups}

    def current_group(self):
        # Only state (for current_group_id) and groups are needed here —
        # players/teams are irrelevant to this endpoint.
        state = self.repository.load_state()
        groups = self.repository.load_groups()
        gid = state.get("current_group_id")
        group = next((g for g in groups if str(g.get("group_id")) == str(gid)), None)
        return {"success": True, "message": "Current group loaded.", "data": group}

    def history(self):
        state = self.repository.load_state()
        return {"success": True, "message": "History loaded.", "data": state.get("history", [])}

    def statistics(self):
        # teams.json is never used below — skip loading it.
        players = self.repository.load_players()
        groups = self.repository.load_groups()
        state = self.repository.load_state()

        sold = [p for p in players if p.get("status") == "sold"]
        held = [g for g in groups if g.get("status") == "held"]
        round2_ids = {str(pid) for g in groups if g.get("round") == 2 for pid in (g.get("players") or [])}
        round2 = [p for p in players if str(p.get("id")) in round2_ids]
        sales = [
            h for h in state.get("history", [])
            if h.get("event") == "SOLD"
        ]

        return {
            "success": True,
            "message": "Statistics loaded.",
            "data": {
                "registered_players": len(players),
                "sold_players": len(sold),
                "available_players": len([p for p in players if p.get("status") == "available"]),
                "held_lots": len(held),
                "round2_players": len({p.get("id") for p in round2}),
                "current_round": state.get("current_round", 1),
                "highest_sale": max((int(s.get("amount", 0)) for s in sales), default=0),
                "total_money_spent": sum(int(s.get("amount", 0)) for s in sales),
            },
        }
