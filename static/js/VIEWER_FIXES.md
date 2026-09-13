# Viewer Fixes — Option 7

Fixed:
1. `/api/state` now includes players, so the Viewer no longer tries to render player images from a payload that did not contain players.
2. Player images use the real `photo_url` from players.json and have an explicit fallback if an image fails.
3. Team cards read the persisted `team.players` array on every 500ms poll.
4. Team purse is read from the persisted `team.purse` after each sale, so the updated remaining purse is shown immediately.
5. SOLD screen uses the persisted SOLD history event and the persisted winning team/player state.
6. SOLD screen also shows a team-by-team squad strip, making the post-sale purchase visible immediately.
7. Sponsor media is loaded from `/api/viewer/media` using `logo_url`.
8. Viewer remains read-only; no auction business logic was moved into the frontend.
