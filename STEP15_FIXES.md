# Step 15 — Viewer Contrast + Persistent Bid Increment

## Fix 1 — Viewer readability
Important Viewer content now sits on explicit high-contrast surfaces:
- live lot header
- player names/details
- current bid
- leading team
- team summary
- waiting message
- SOLD screen
- team-wise sold summary
- pause/completed screens

The background remains visible but is deliberately subdued behind text.

## Fix 2 — Bid increment persistence
A dedicated authenticated API:
`POST /api/auction/increment`

now persists the Auctioneer's selected increment to `auction_state.json`.

Supported quick increments:
- 50
- 100
- 200
- 500
- 1000

Custom values must be multiples of 50.

The selected increment survives the 500ms dashboard refresh cycle and is used
for the next team selection.

## Fix 3 — Base price + increment behavior
The first team that accepts a selected lot gets the lot at its base price.
Every subsequent team selection automatically adds the persisted selected
increment.

Example:
Base ₹5,000 + increment ₹1,000:
Team A → ₹5,000
Team B → ₹6,000
Team C → ₹7,000

The backend remains authoritative.
