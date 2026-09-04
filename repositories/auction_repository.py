from pathlib import Path
from storage.json_storage import read_json, write_many_atomic

class AuctionRepository:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)

    def path(self, name):
        return self.data_dir / name

    def load_all(self):
        return {
            "players": read_json(self.path("players.json"), []),
            "teams": read_json(self.path("teams.json"), []),
            "groups": read_json(self.path("auction_groups.json"), []),
            "state": read_json(self.path("auction_state.json"), {}),
        }

    def save_all(self, documents):
        write_many_atomic({
            self.path("players.json"): documents["players"],
            self.path("teams.json"): documents["teams"],
            self.path("auction_groups.json"): documents["groups"],
            self.path("auction_state.json"): documents["state"],
        })

    def save_state(self, state):
        from storage.json_storage import write_json
        write_json(self.path("auction_state.json"), state)

    def save_groups_and_state(self, groups, state):
        write_many_atomic({
            self.path("auction_groups.json"): groups,
            self.path("auction_state.json"): state,
        })
