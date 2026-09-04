"""MPL Season 2 SELL transaction.

The sale operation is deliberately isolated because it is the highest-risk
mutation in the auction.

Before mutating anything it:
1. Validates the active lot and leading team.
2. Validates all referenced players.
3. Validates the final price against the team's purse.
4. Captures a complete pre-sale snapshot.
5. Produces updated players, teams, groups and state.
6. Records the sale in state history.

The caller should persist the returned documents through the Step 2 atomic
storage layer. If persistence fails, the pre-sale snapshot can be restored.
"""

from copy import deepcopy
from datetime import datetime


class SaleError(ValueError):
    pass


class SaleService:
    def __init__(self, players, teams, groups, state):
        self.players = deepcopy(players)
        self.teams = deepcopy(teams)
        self.groups = deepcopy(groups)
        self.state = deepcopy(state)

    def _player(self, player_id):
        return next((p for p in self.players if str(p.get("id")) == str(player_id)), None)

    def _team(self, team_id):
        return next((t for t in self.teams if str(t.get("id")) == str(team_id)), None)

    def _group(self, group_id):
        return next((g for g in self.groups if str(g.get("group_id")) == str(group_id)), None)

    def _timestamp(self):
        return datetime.now().strftime("%H:%M:%S")

    def sell(self):
        state = self.state
        if not state.get("auction_started"):
            raise SaleError("Auction has not started.")
        if state.get("auction_finished") or state.get("auction_status") == "COMPLETED":
            raise SaleError("Auction is already completed.")
        if state.get("auction_status") != "LIVE_BIDDING":
            raise SaleError("Lot is not currently live.")

        group_id = state.get("current_group_id")
        if not group_id:
            raise SaleError("No current auction group.")

        group = self._group(group_id)
        if not group:
            raise SaleError("Current auction group does not exist.")
        if group.get("status") == "sold":
            raise SaleError("Auction group is already sold.")
        if group.get("status") in {"invalid"}:
            raise SaleError("Auction group is invalid.")

        bid = state.get("current_bid") or {}
        winner_id = bid.get("team_id")
        final_price = int(bid.get("amount") or 0)

        if not winner_id:
            raise SaleError("Cannot sell without a leading team.")
        if final_price <= 0:
            raise SaleError("Final bid must be greater than zero.")

        team = self._team(winner_id)
        if not team:
            raise SaleError("Winning team does not exist.")

        purse = int(team.get("purse", 0))
        if final_price > purse:
            raise SaleError("Insufficient purse for the final sale price.")

        player_ids = group.get("players") or []
        if not player_ids:
            raise SaleError("Auction group contains no players.")

        resolved_players = []
        for pid in player_ids:
            player = self._player(pid)
            if not player:
                raise SaleError(f"Player {pid} does not exist.")
            if player.get("status") == "sold":
                raise SaleError(f"Player {pid} is already sold.")
            if player.get("team_id") is not None:
                raise SaleError(f"Player {pid} is already assigned to a team.")
            resolved_players.append(player)

        # Complete pre-sale snapshot. This is intentionally independent from
        # transaction history so rollback restores exact pre-sale documents.
        snapshot = {
            "players": deepcopy(self.players),
            "teams": deepcopy(self.teams),
            "auction_groups": deepcopy(self.groups),
            "auction_state": deepcopy(self.state),
        }

        # Apply player updates.
        for player in resolved_players:
            player["status"] = "sold"
            player["team_id"] = winner_id

        # Apply team updates.
        existing_team_players = list(team.get("players") or [])
        for pid in player_ids:
            if pid not in existing_team_players:
                existing_team_players.append(pid)
        team["players"] = existing_team_players
        team["purse"] = purse - final_price

        # Apply group updates.
        group["status"] = "sold"
        group["winner_team_id"] = winner_id
        group["current_bid"] = final_price

        # Apply auction-state updates.
        state["auction_status"] = "LOT_SOLD"
        state["last_sale_snapshot"] = snapshot
        state["history"] = list(state.get("history") or [])
        state["history"].append({
            "timestamp": self._timestamp(),
            "event": "SOLD",
            "group_id": group_id,
            "team_id": winner_id,
            "amount": final_price,
            "players": list(player_ids),
        })

        return {
            "success": True,
            "message": "Lot sold successfully.",
            "data": {
                "players": deepcopy(self.players),
                "teams": deepcopy(self.teams),
                "auction_groups": deepcopy(self.groups),
                "auction_state": deepcopy(state),
                "sale": {
                    "group_id": group_id,
                    "team_id": winner_id,
                    "amount": final_price,
                    "players": list(player_ids),
                },
                "pre_sale_snapshot": snapshot,
            }
        }
