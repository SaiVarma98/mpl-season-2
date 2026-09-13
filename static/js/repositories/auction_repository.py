import time
import threading
from pathlib import Path
from storage.json_storage import read_json, write_json, write_many_atomic


class _TTLCache:
    """Tiny read-coalescing cache.

    With ~250 viewers each polling /api/state roughly once a second, most
    of those requests land within the same fraction of a second asking for
    identical data. Without this, every single one of them re-reads and
    re-parses all four JSON files from disk. With it, only the first
    request after something actually changes pays that cost - everyone
    else within the TTL window gets the same already-parsed result.

    Any write calls invalidate(), which clears the cache immediately, so
    the auctioneer's own next read after an action is always fully fresh.
    Only concurrent VIEWER reads *between* two writes ever share a cached
    copy, and never for longer than `ttl_seconds`.

    IMPORTANT: this cache lives in this process's memory only, same as the
    storage lock in json_storage.py. It is only correct when the app runs
    as a single process (e.g. `gunicorn --workers 1 --threads N`). Running
    multiple worker PROCESSES would give each one its own independent
    cache and its own independent lock, so reads/writes across processes
    would no longer be consistent with each other. Don't scale this past
    one process without also moving the cache/lock to something shared
    across processes (Redis, a real database, etc).
    """

    def __init__(self, ttl_seconds=0.4):
        self.ttl = ttl_seconds
        self._lock = threading.Lock()
        self._store = {}

    def get_or_load(self, key, loader):
        now = time.monotonic()
        with self._lock:
            hit = self._store.get(key)
            if hit is not None and hit[0] > now:
                return hit[1]
        value = loader()
        with self._lock:
            self._store[key] = (now + self.ttl, value)
        return value

    def invalidate(self):
        with self._lock:
            self._store.clear()


class AuctionRepository:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self._cache = _TTLCache()

    def path(self, name):
        return self.data_dir / name

    def load_all(self):
        return self._cache.get_or_load("all", lambda: {
            "players": read_json(self.path("players.json"), []),
            "teams": read_json(self.path("teams.json"), []),
            "groups": read_json(self.path("auction_groups.json"), []),
            "state": read_json(self.path("auction_state.json"), {}),
        })

    def load_players(self):
        return self._cache.get_or_load(
            "players", lambda: read_json(self.path("players.json"), [])
        )

    def load_groups(self):
        return self._cache.get_or_load(
            "groups", lambda: read_json(self.path("auction_groups.json"), [])
        )

    def load_state(self):
        return self._cache.get_or_load(
            "state", lambda: read_json(self.path("auction_state.json"), {})
        )

    def save_all(self, documents):
        write_many_atomic({
            self.path("players.json"): documents["players"],
            self.path("teams.json"): documents["teams"],
            self.path("auction_groups.json"): documents["groups"],
            self.path("auction_state.json"): documents["state"],
        })
        self._cache.invalidate()

    def save_state(self, state):
        write_json(self.path("auction_state.json"), state)
        self._cache.invalidate()

    def save_groups_and_state(self, groups, state):
        write_many_atomic({
            self.path("auction_groups.json"): groups,
            self.path("auction_state.json"): state,
        })
        self._cache.invalidate()
