"""MPL Season 2 global auction lifecycle controls.

Implements:
- PAUSE
- RESUME
- RESET + backup
- END AUCTION

The service validates lifecycle operations and returns complete documents for
the repository/storage layer to persist. It does not perform HTTP handling.
"""

from copy import deepcopy
from datetime import datetime


class LifecycleError(ValueError):
    pass


WAITING_FOR_GROUP = "WAITING_FOR_GROUP"
LIVE_BIDDING = "LIVE_BIDDING"
LOT_SOLD = "LOT_SOLD"
PAUSED = "PAUSED"
ROUND_2 = "ROUND_2"
COMPLETED = "COMPLETED"


def _timestamp():
    return datetime.now().strftime("%H:%M:%S")


class LifecycleService:
    def __init__(self, players, teams, groups, state):
        self.players = deepcopy(players)
        self.teams = deepcopy(teams)
        self.groups = deepcopy(groups)
        self.state = deepcopy(state)

    def _event(self, event, **extra):
        record = {"timestamp": _timestamp(), "event": event}
        record.update(extra)
        self.state.setdefault("history", []).append(record)

    def pause(self):
        if not self.state.get("auction_started"):
            raise LifecycleError("Auction has not started.")
        if self.state.get("auction_finished") or self.state.get("auction_status") == COMPLETED:
            raise LifecycleError("Auction is already completed.")
        if self.state.get("auction_status") != LIVE_BIDDING:
            raise LifecycleError("Auction can only be paused during live bidding.")

        self.state["auction_status"] = PAUSED
        self._event(
            "PAUSE",
            group_id=self.state.get("current_group_id"),
            amount=self.state.get("current_bid", {}).get("amount", 0),
            team_id=self.state.get("current_bid", {}).get("team_id"),
        )
        return self.result("Auction paused.")

    def resume(self):
        if not self.state.get("auction_started"):
            raise LifecycleError("Auction has not started.")
        if self.state.get("auction_finished") or self.state.get("auction_status") == COMPLETED:
            raise LifecycleError("Auction is already completed.")
        if self.state.get("auction_status") != PAUSED:
            raise LifecycleError("Auction is not paused.")

        self.state["auction_status"] = LIVE_BIDDING
        self._event(
            "RESUME",
            group_id=self.state.get("current_group_id"),
            amount=self.state.get("current_bid", {}).get("amount", 0),
            team_id=self.state.get("current_bid", {}).get("team_id"),
        )
        return self.result("Auction resumed.")

    def end(self):
        if not self.state.get("auction_started"):
            raise LifecycleError("Auction has not started.")
        if self.state.get("auction_finished") or self.state.get("auction_status") == COMPLETED:
            raise LifecycleError("Auction is already completed.")
        if self.state.get("auction_status") == LIVE_BIDDING:
            raise LifecycleError("Cannot end auction while a lot is live.")
        if self.state.get("auction_status") == PAUSED:
            raise LifecycleError("Resume the auction before ending it.")

        self.state["auction_finished"] = True
        self.state["auction_status"] = COMPLETED
        self.state["current_group_id"] = None
        self.state["current_bid"] = {"amount": 0, "team_id": None}

        self._event("AUCTION_COMPLETED")
        return self.result("Auction completed.")

    def reset(self, create_backup, confirm=True):
        if not confirm:
            raise LifecycleError("Reset confirmation is required.")

        # Backup is deliberately performed before any mutation.
        backup_dir = create_backup(
            self.players,
            self.teams,
            self.groups,
            self.state,
        )

        reset_players = deepcopy(self.players)
        for player in reset_players:
            player["status"] = "available"
            player["team_id"] = None

        reset_teams = deepcopy(self.teams)
        for team in reset_teams:
            team["purse"] = int(team.get("default_purse", 0))
            team["players"] = []

        reset_groups = deepcopy(self.groups)
        for group in reset_groups:
            group["status"] = "pending"
            group["current_bid"] = 0
            group["winner_team_id"] = None

        reset_state = {
            "auction_started": False,
            "auction_finished": False,
            "current_round": 1,
            "auction_status": WAITING_FOR_GROUP,
            "current_group_id": None,
            "current_bid": {"amount": 0, "team_id": None},
            "bid_increment": 1000,
            "last_sale_snapshot": None,
            "history": [
                {
                    "timestamp": _timestamp(),
                    "event": "RESET",
                }
            ],
        }

        return {
            "success": True,
            "message": "Auction reset successfully.",
            "data": {
                "players": reset_players,
                "teams": reset_teams,
                "auction_groups": reset_groups,
                "auction_state": reset_state,
                "backup_dir": str(backup_dir),
            },
        }

    def result(self, message):
        return {
            "success": True,
            "message": message,
            "data": {
                "players": deepcopy(self.players),
                "teams": deepcopy(self.teams),
                "auction_groups": deepcopy(self.groups),
                "auction_state": deepcopy(self.state),
            },
        }
