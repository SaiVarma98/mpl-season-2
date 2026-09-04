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


class APIService:
    def __init__(self, repository):
        self.repository = repository

    def _engine(self):
        docs = self.repository.load_all()
        return AuctionEngine(
            docs["players"], docs["teams"], docs["groups"], docs["state"]
        )

    def start(self):
        engine = self._engine()
        result = engine.start()
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["groups"],
            "state": result["data"]["state"],
        })
        return result

    def select(self, group_id):
        engine = self._engine()
        result = engine.select_group(group_id)
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["groups"],
            "state": result["data"]["state"],
        })
        return result


    def restart_current_lot(self):
        engine = self._engine()
        result = engine.restart_current_lot()
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["groups"],
            "state": result["data"]["state"],
        })
        return result

    def set_increment(self, increment):
        engine = self._engine()
        result = engine.set_increment(increment)
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["groups"],
            "state": result["data"]["state"],
        })
        return result

    def bid(self, team_id):
        engine = self._engine()
        result = engine.bid(team_id)
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["groups"],
            "state": result["data"]["state"],
        })
        return result

    def sell(self):
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
        docs = self.repository.load_all()
        result = LotFlowService(docs["groups"], docs["state"]).pass_lot()
        self.repository.save_groups_and_state(
            result["data"]["groups"], result["data"]["auction_state"]
        )
        return result

    def hold_lot(self):
        docs = self.repository.load_all()
        result = LotFlowService(docs["groups"], docs["state"]).hold_lot()
        self.repository.save_groups_and_state(
            result["data"]["groups"], result["data"]["auction_state"]
        )
        return result

    def pause(self):
        docs = self.repository.load_all()
        result = LifecycleService(
            docs["players"], docs["teams"], docs["groups"], docs["state"]
        ).pause()
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["auction_groups"],
            "state": result["data"]["auction_state"],
        })
        return result

    def resume(self):
        docs = self.repository.load_all()
        result = LifecycleService(
            docs["players"], docs["teams"], docs["groups"], docs["state"]
        ).resume()
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["auction_groups"],
            "state": result["data"]["auction_state"],
        })
        return result

    def round2(self):
        docs = self.repository.load_all()
        result = LotFlowService(docs["groups"], docs["state"]).start_round_2()
        self.repository.save_groups_and_state(
            result["data"]["groups"], result["data"]["auction_state"]
        )
        return result

    def end(self):
        docs = self.repository.load_all()
        result = LifecycleService(
            docs["players"], docs["teams"], docs["groups"], docs["state"]
        ).end()
        self.repository.save_all({
            "players": result["data"]["players"],
            "teams": result["data"]["teams"],
            "groups": result["data"]["auction_groups"],
            "state": result["data"]["auction_state"],
        })
        return result

    def reset(self, backup_func):
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
        docs = self.repository.load_all()
        return {"success": True, "message": "Players loaded.", "data": docs["players"]}

    def groups(self):
        docs = self.repository.load_all()
        return {"success": True, "message": "Groups loaded.", "data": docs["groups"]}

    def current_group(self):
        docs = self.repository.load_all()
        gid = docs["state"].get("current_group_id")
        group = next((g for g in docs["groups"] if str(g.get("group_id")) == str(gid)), None)
        return {"success": True, "message": "Current group loaded.", "data": group}

    def history(self):
        docs = self.repository.load_all()
        return {"success": True, "message": "History loaded.", "data": docs["state"].get("history", [])}

    def statistics(self):
        docs = self.repository.load_all()
        players = docs["players"]
        groups = docs["groups"]
        state = docs["state"]

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
