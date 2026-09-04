from pathlib import Path
from storage.json_storage import read_json

class UserRepository:
    def __init__(self, data_dir):
        self.path = Path(data_dir) / "users.json"

    def find(self, username):
        users = read_json(self.path, [])
        return next(
            (u for u in users if str(u.get("username")) == str(username)),
            None
        )
