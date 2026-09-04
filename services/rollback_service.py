"""Last-sale rollback support."""

from copy import deepcopy


class RollbackError(ValueError):
    pass


def rollback_last_sale(state):
    snapshot = state.get("last_sale_snapshot")
    if not snapshot:
        raise RollbackError("No completed sale is available for rollback.")

    required = {"players", "teams", "auction_groups", "auction_state"}
    if not required.issubset(snapshot):
        raise RollbackError("Last-sale snapshot is incomplete.")

    restored = deepcopy(snapshot["auction_state"])
    history = list(restored.get("history") or [])
    history.append({
        "timestamp": __import__("datetime").datetime.now().strftime("%H:%M:%S"),
        "event": "ROLLBACK",
        "group_id": snapshot["auction_state"].get("current_group_id"),
    })
    restored["history"] = history
    # A rollback itself must not retain the snapshot as an active undo chain.
    restored["last_sale_snapshot"] = None

    return {
        "success": True,
        "message": "Last sale rolled back successfully.",
        "data": {
            "players": deepcopy(snapshot["players"]),
            "teams": deepcopy(snapshot["teams"]),
            "auction_groups": deepcopy(snapshot["auction_groups"]),
            "auction_state": restored,
        }
    }
