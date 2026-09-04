"""MPL Season 2 Auction Engine — Step 4.

Implements:
- Start auction
- Select group
- Bid with fixed/custom increments
- Base-price validation
- Team purse validation
- Leading-team updates
- Bid history

This step deliberately does NOT perform a sale. Sale is the next critical
transaction step, where players, teams, groups and auction state must be
updated together with a pre-sale snapshot.
"""

from copy import deepcopy
from datetime import datetime

from services.auction_state_machine import AuctionStateMachine, StateTransitionError
from models.auction_state import WAITING_FOR_GROUP, LIVE_BIDDING, ROUND_2


class AuctionError(ValueError):
    pass


ALLOWED_INCREMENTS = {50, 100, 200, 500, 1000}


class AuctionEngine:
    def __init__(self, players, teams, groups, state):
        self.players = deepcopy(players)
        self.teams = deepcopy(teams)
        self.groups = deepcopy(groups)
        self.state = deepcopy(state)

    def _machine(self):
        return AuctionStateMachine(self.state)

    def _now(self):
        return datetime.now().strftime("%H:%M:%S")

    def _event(self, event, **extra):
        record = {"timestamp": self._now(), "event": event}
        record.update(extra)
        self.state.setdefault("history", []).append(record)

    def _team(self, team_id):
        return next((t for t in self.teams if str(t.get("id")) == str(team_id)), None)

    def _group(self, group_id):
        return next((g for g in self.groups if str(g.get("group_id")) == str(group_id)), None)

    def _validate_group_players(self, group):
        if not group.get("players"):
            raise AuctionError("Auction group contains no players.")

        known_ids = {str(p.get("id")) for p in self.players}
        for player_id in group["players"]:
            if str(player_id) not in known_ids:
                raise AuctionError(f"Player {player_id} does not exist.")

    def start(self):
        sm = self._machine()
        try:
            self.state = sm.start()
        except StateTransitionError as exc:
            raise AuctionError(str(exc)) from exc

        self._event("AUCTION_STARTED")
        return self.result("Auction started successfully.")

    def select_group(self, group_id):
        group = self._group(group_id)
        if not group:
            raise AuctionError("Auction group not found.")

        self._validate_group_players(group)

        if group.get("status") in {"sold", "invalid"}:
            raise AuctionError("This auction group cannot be selected.")

        sm = self._machine()
        try:
            self.state = sm.select_group(group)
        except StateTransitionError as exc:
            raise AuctionError(str(exc)) from exc

        # The lot opens at its base price. No team is leading until a team
        # accepts that opening price. The Auctioneer's selected increment is
        # used automatically for subsequent team bids.
        base_price = int(group.get("base_price", 0))
        self.state["current_bid"] = {
            "amount": base_price,
            "team_id": None,
        }
        self.state["bid_increment"] = int(self.state.get("bid_increment", 1000) or 1000)

        self._event(
            "GROUP_SELECTED",
            group_id=group["group_id"],
            round=self.state["current_round"],
            base_price=int(group.get("base_price", 0)),
        )
        return self.result("Auction group selected successfully.")


    def restart_current_lot(self):
        group_id = self.state.get("current_group_id")
        if not group_id:
            raise AuctionError("There is no current lot to restart.")
        if self.state.get("auction_status") != LIVE_BIDDING:
            raise AuctionError("Only a live, unsold lot can be restarted.")
        group = self._group(group_id)
        if not group:
            raise AuctionError("Current auction group was not found.")
        if group.get("status") == "sold":
            raise AuctionError("A sold lot cannot be restarted.")
        base_price = int(group.get("base_price", 0))
        self.state["current_bid"] = {"amount": base_price, "team_id": None}
        group["current_bid"] = base_price
        group["winner_team_id"] = None
        self._event("CURRENT_LOT_RESTARTED", group_id=group_id, base_price=base_price)
        return self.result(f"Current lot restarted at ₹{base_price:,}.")

    def set_increment(self, increment):
        try:
            increment = int(increment)
        except (TypeError, ValueError) as exc:
            raise AuctionError("Bid increment must be a positive number.") from exc

        if increment < 50 or increment % 50 != 0:
            raise AuctionError("Bid increment must be a multiple of ₹50.")
        self.state["bid_increment"] = increment
        self._event("BID_INCREMENT_CHANGED", increment=increment)
        return self.result(f"Bid increment set to ₹{increment:,}.")

    def bid(self, team_id):
        if not team_id:
            raise AuctionError("Team ID is required.")

        increment = int(self.state.get("bid_increment", 1000) or 1000)
        if increment < 50 or increment % 50 != 0:
            raise AuctionError("Stored bid increment is invalid. Set a valid increment before bidding.")

        group_id = self.state.get("current_group_id")
        group = self._group(group_id)
        if not group:
            raise AuctionError("No current auction group.")

        team = self._team(team_id)
        if not team:
            raise AuctionError("Invalid team.")

        status = self.state.get("auction_status")
        if status != LIVE_BIDDING:
            raise AuctionError("Bidding is not currently active.")

        current = int(self.state.get("current_bid", {}).get("amount", 0))
        base_price = int(group.get("base_price", 0))
        leading_team = self.state.get("current_bid", {}).get("team_id")

        # The first team to accept the lot gets it at the base price.
        # The configured increment is only applied after a leading team exists.
        if not leading_team:
            new_bid = base_price
        else:
            new_bid = current + increment

        purse = int(team.get("purse", 0))
        if new_bid > purse:
            raise AuctionError(
                f"Insufficient purse. {team.get('team_name', team_id)} has "
                f"₹{purse:,} remaining."
            )

        if leading_team and str(leading_team) == str(team_id):
            raise AuctionError("The leading team cannot bid against itself.")

        try:
            self.state = self._machine().set_bid(str(team_id), new_bid)
        except StateTransitionError as exc:
            raise AuctionError(str(exc)) from exc

        # Keep the group-side current bid synchronized with the live state.
        group["current_bid"] = new_bid

        self._event(
            "BID",
            group_id=group_id,
            team_id=str(team_id),
            amount=new_bid,
            increment=increment,
        )
        return self.result("Bid accepted successfully.")

    def result(self, message):
        return {
            "success": True,
            "message": message,
            "data": {
                "players": deepcopy(self.players),
                "teams": deepcopy(self.teams),
                "groups": deepcopy(self.groups),
                "state": deepcopy(self.state),
            },
        }
