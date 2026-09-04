# Step 18 — Viewer Connection Fix + Restart Current Lot

## Viewer connection lost
The connection overlay previously had an author CSS `display:flex` rule that could override the HTML `hidden` attribute. A global `[hidden]{display:none!important}` rule now guarantees the overlay is actually hidden after a successful poll. The Viewer also polls `/api/state` and `/api/players`, with groups and teams taken from the state response, reducing the number of simultaneous requests.

## Restart current unsold lot
Auctioneer now has `RESTART CURRENT LOT`. It is available only while a lot is live and unsold. It:
- keeps the same group selected
- resets current bid to the lot base price
- clears the leading team
- does not change team purses
- does not mark players sold
- records `CURRENT_LOT_RESTARTED` in history
- persists immediately

This is a single-lot restart, not a full auction reset.
