from pathlib import Path
from datetime import datetime
import shutil


def create_auction_backup(players, teams, groups, state):
    # API Step 8 receives the documents already loaded by the repository.
    # The production integration should pass the actual data directory and
    # copy those four JSON files before reset. This helper is intentionally
    # simple and self-contained for the API scaffold.
    backup_root = Path(__file__).resolve().parents[1] / 'backups'
    backup_dir = backup_root / datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_dir.mkdir(parents=True, exist_ok=False)

    docs = {
        "players.json": players,
        "teams.json": teams,
        "auction_groups.json": groups,
        "auction_state.json": state,
    }
    import json
    for filename, data in docs.items():
        (backup_dir / filename).write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
    return backup_dir
